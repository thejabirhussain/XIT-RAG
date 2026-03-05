from typing import Any

from services.rag2_services import RouterService, MSSQLService, Text2SQLService, LLM2Service
from models.rag2_models import Rag2ChatResponse, SqlResult, VectorSource

# Confidence threshold below which we always use hybrid
HYBRID_CONFIDENCE_THRESHOLD = 0.80

# Qdrant collection name for compliance framework documents
# Set COMPLIANCE_COLLECTION in .env to override
import os
COMPLIANCE_COLLECTION = os.getenv("COMPLIANCE_COLLECTION", "compliance_docs")


class Query2Handler:
    def __init__(
        self,
        router_service: RouterService,
        text2sql_service: Text2SQLService,
        mssql_service: MSSQLService,
        llm2_service: LLM2Service,
        embedding_service,      # reused from existing EmbeddingService
        retrieval_service,      # reused from existing RetrievalService
    ):
        self.router = router_service
        self.text2sql = text2sql_service
        self.mssql = mssql_service
        self.llm2 = llm2_service
        self.embedder = embedding_service
        self.retrieval = retrieval_service

    def handle_query(
        self,
        query: str,
        org_id: int,
        model: str = "gemini",
        force_route: str | None = None,
        top_k_docs: int = 5,
    ) -> Rag2ChatResponse:

        # ── Step 1: Route Classification ──────────────────────────────────
        if force_route:
            route, confidence = force_route, 1.0
        else:
            route, confidence = self.router.classify(query)
            # Low confidence → always go hybrid to avoid dropping context
            if confidence < HYBRID_CONFIDENCE_THRESHOLD and route != "hybrid":
                route = "hybrid"

        sql_result: SqlResult | None = None
        vector_sources: list[VectorSource] = []
        context_parts: list[str] = []

        # ── Step 2a: Structured SQL Path ──────────────────────────────────
        if route in ("structured", "hybrid"):
            try:
                # Step 2a: Retrieve relevant schema chunks from Qdrant
                schema_vec = self.embedder.embed(query)
                schema_chunks = self.retrieval.retrieve(
                    collection="compliance_schema",   # ← separate collection for schema docs
                    query_vec=schema_vec,
                    top_k=4,
                    cutoff=0.20,
                )
                schema_context = "\n\n".join(c["text"] for c in schema_chunks)

                # Then generate SQL with only those tables
                sql = self.text2sql.generate_sql(query, org_id, schema_context)

                #sql = self.text2sql.generate_sql(query, org_id)
                rows = self.mssql.execute_query(sql)
                sql_result = SqlResult(
                    generated_sql=sql,
                    row_count=len(rows),
                    rows=rows,
                )
                context_parts.append(
                    self.llm2.format_sql_context(sql, rows)
                )
            except Exception as e:
                # Don't fail the whole request — log and continue to knowledge path
                context_parts.append(f"[SQL PATH ERROR: {str(e)}]")

        # ── Step 2b: Knowledge / Vector Path ──────────────────────────────
        if route in ("knowledge", "hybrid"):
            try:
                #query_vec = self.embedder.embed(query)
                # CORRECT — matches EmbeddingService.get_embedding()
                query_vec = self.embedder.get_embedding(query)
                chunks = self.retrieval.retrieve(
                    collection=COMPLIANCE_COLLECTION,
                    query_vec=query_vec,
                    top_k=top_k_docs,
                    cutoff=0.22,
                )
                if chunks:
                    reranked = self.retrieval.rerank(query, chunks, top_n=3)
                    vector_sources = [
                        VectorSource(
                            score=float(c.get("score", 0.0)),
                            title=c.get("title", ""),
                            text=c.get("text", ""),
                            url=c.get("url"),
                            section_heading=c.get("section_heading"),
                        )
                        for c in reranked
                    ]
                    context_parts.append(
                        self.llm2.format_vector_context(reranked)
                    )
            except Exception as e:
                context_parts.append(f"[VECTOR PATH ERROR: {str(e)}]")

        # ── Step 3: Generate Final Answer ─────────────────────────────────
        full_context = "\n\n---\n\n".join(context_parts) if context_parts else "No context available."
        answer = self.llm2.generate_answer(
            query=query,
            context=full_context,
            org_id=org_id,
            model=model,
        )

        return Rag2ChatResponse(
            query=query,
            org_id=org_id,
            route=route,
            confidence=confidence,
            answer=answer,
            sql_result=sql_result,
            vector_sources=vector_sources if vector_sources else None,
        )
