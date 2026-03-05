import re
import io
import uuid
import logging
from typing import Any

import pdfplumber
import numpy as np
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)

_TABLE_MARKER    = re.compile(r"\[TABLE:\s*(\w+)\]")
_SECTION_MARKER  = re.compile(r"\[SECTION:\s*([\w_]+)\]")
_NLP_KEYWORDS_RE = re.compile(r"NLP KEYWORDS:\s*(.+)", re.IGNORECASE)
_PURPOSE_RE      = re.compile(r"PURPOSE:\s*(.+)", re.IGNORECASE)

KEEP_SECTIONS = {
    "overview",
    "column_definitions",
    "keys_and_constraints",
    "sql_examples",
    "rag_retrieval_hints",
    "foreign_key_reference_map",
    "constraints_and_generated_columns",
    "data_flow_lifecycles",
}


class SchemaIngestionService:
    def __init__(self, qdrant_service, embedding_service):
        """
        qdrant_service:   existing QdrantService instance
        embedding_service: existing EmbeddingService instance
        """
        self.qdrant_service   = qdrant_service
        self.embedding_service = embedding_service

    # ── PDF Text Extraction ────────────────────────────────────────────────────

    def _extract_text(self, source: str | bytes) -> str:
        opener = (
            pdfplumber.open(source)
            if isinstance(source, str)
            else pdfplumber.open(io.BytesIO(source))
        )
        pages = []
        with opener as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
        return "\n\n".join(pages)

    # ── Chunking ───────────────────────────────────────────────────────────────

    def _parse_chunks(self, raw_text: str) -> list[dict[str, Any]]:
        lines = raw_text.split("\n")

        current_table: str | None   = None
        current_section: str | None = None

        # { table_name: { section_name: [lines] } }
        table_buffers: dict[str, dict[str, list[str]]] = {}
        # { table_name: { "nlp_keywords": "...", "purpose": "..." } }
        table_metadata: dict[str, dict[str, str]] = {}

        for line in lines:
            table_match = _TABLE_MARKER.search(line)

            if table_match:
                raw_table = table_match.group(1).lower()
                # [TABLE: DOCUMENT] → use __document__ as key
                current_table = "__document__" if raw_table == "document" else raw_table

                section_match = _SECTION_MARKER.search(line)
                current_section = section_match.group(1).lower() if section_match else "overview"

                table_buffers.setdefault(current_table, {})
                table_metadata.setdefault(current_table, {"nlp_keywords": "", "purpose": ""})
                table_buffers[current_table].setdefault(current_section, [])
                continue

            if not current_table:
                continue

            stripped = line.strip()

            kw_match = _NLP_KEYWORDS_RE.match(stripped)
            if kw_match:
                table_metadata[current_table]["nlp_keywords"] = kw_match.group(1).strip()
                continue

            purpose_match = _PURPOSE_RE.match(stripped)
            if purpose_match and not table_metadata[current_table]["purpose"]:
                table_metadata[current_table]["purpose"] = purpose_match.group(1).strip()

            table_buffers[current_table].setdefault(current_section, []).append(line)

        # ── Assemble one chunk per table ───────────────────────────────────────
        chunks: list[dict[str, Any]] = []
        for table_name, sections in table_buffers.items():
            included = {
                k: [l for l in v if l.strip()]
                for k, v in sections.items()
                if k in KEEP_SECTIONS and any(l.strip() for l in v)
            }
            if not included:
                continue

            section_blocks = [
                f"[SECTION: {k.upper()}]\n" + "\n".join(v)
                for k, v in included.items()
            ]
            full_text = f"[TABLE: {table_name}]\n" + "\n\n".join(section_blocks)

            meta        = table_metadata.get(table_name, {})
            nlp_keywords = meta.get("nlp_keywords", "")
            purpose      = meta.get("purpose", "")

            # embed_text = keywords + purpose + schema text (richer signal for retrieval)
            embed_text = "\n".join(filter(None, [nlp_keywords, purpose, full_text]))

            chunks.append({
                "table_name":    table_name,
                "nlp_keywords":  nlp_keywords,
                "purpose":       purpose,
                "text":          full_text,
                "embed_text":    embed_text,
                "chunk_type":    "schema_table",
                "schema_name":   "compliance_platform_v3",
            })

        logger.info(f"[SchemaIngestion] Parsed {len(chunks)} table chunks")
        return chunks

    # ── Qdrant Upsert ──────────────────────────────────────────────────────────

    def _upsert_chunks(self, collection_name: str, chunks: list[dict[str, Any]]) -> int:
        points: list[PointStruct] = []

        for chunk in chunks:
            # Use the same EmbeddingService method as the rest of the codebase
            vec: np.ndarray = self.embedding_service.get_embedding(chunk["embed_text"])

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec.tolist(),
                    payload={
                        "table_name":   chunk["table_name"],
                        "nlp_keywords": chunk["nlp_keywords"],
                        "purpose":      chunk["purpose"],
                        "text":         chunk["text"],
                        "chunk_type":   chunk["chunk_type"],
                        "schema_name":  chunk["schema_name"],
                        # mirror the fields retrieval_service.py reads from payload
                        "title":        f"Schema: {chunk['table_name']}",
                        "url":          "",
                        "section_heading": chunk["table_name"],
                    },
                )
            )

        # Use qdrant_service.client.upsert — same pattern as ingestion_service.py
        self.qdrant_service.client.upsert(collection_name=collection_name, points=points)
        logger.info(f"[SchemaIngestion] Upserted {len(points)} points → '{collection_name}'")
        return len(points)

    # ── Public API ─────────────────────────────────────────────────────────────

    def ingest(
        self,
        source: str | bytes,           # file path (str) or raw bytes
        collection_name: str  = "compliance_schema",
        recreate_collection: bool = False,
    ) -> dict[str, Any]:

        raw_text = self._extract_text(source)
        chunks   = self._parse_chunks(raw_text)

        if not chunks:
            return {
                "status":         "error",
                "message":        "No table chunks parsed from PDF",
                "chunks_stored":  0,
                "collection_name": collection_name,
                "vector_size":    0,
                "tables_parsed":  [],
            }

        # Use embedding_service.vector_size — already computed at startup, no test embed needed
        vector_size: int = self.embedding_service.vector_size

        # Recreate: delete first, then ensure_collection will create fresh
        if recreate_collection:
            existing = [c.name for c in self.qdrant_service.client.get_collections().collections]
            if collection_name in existing:
                self.qdrant_service.client.delete_collection(collection_name)
                logger.info(f"[SchemaIngestion] Deleted collection '{collection_name}' for recreation")

        # ensure_collection is idempotent — skips creation if already exists
        self.qdrant_service.ensure_collection(collection_name, vector_size)

        stored = self._upsert_chunks(collection_name, chunks)

        return {
            "status":          "success",
            "collection_name": collection_name,
            "chunks_stored":   stored,
            "vector_size":     vector_size,
            "tables_parsed":   [c["table_name"] for c in chunks],
            "message":         "",
        }
        # ── Convenience wrappers called by SchemaIngestionHandler ─────────────────

    def ingest_from_bytes(
        self,
        pdf_bytes: bytes,
        collection_name: str = "compliance_schema",
        recreate_collection: bool = False,
    ) -> dict:
        return self.ingest(
            source=pdf_bytes,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )

    def ingest_from_path(
        self,
        pdf_path: str,
        collection_name: str = "compliance_schema",
        recreate_collection: bool = False,
    ) -> dict:
        return self.ingest(
            source=pdf_path,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )
