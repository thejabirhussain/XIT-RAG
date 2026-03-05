from typing import Optional

import numpy as np

from models import ChatResponse, Source
from services.rag_services.retrieval_service import TOP_K, TOP_N, SIMILARITY_CUTOFF

COLLECTION_NAME = "irs_rag_v1"
SCHEMA_COLLECTION = "schema"
NO_KB_MSG = "I don't have verifiable information in the knowledge base for that query."

SCHEMA_KEYWORDS = [
    "table", "column", "foreign key", "sql", "schema",
    "relationship", "compliance", "data model", "query", "database", "risks"
]

def is_schema_query(query: str) -> bool:
    q_lower = query.lower()
    return any(keyword in q_lower for keyword in SCHEMA_KEYWORDS)


class QueryHandler:
    def __init__(
        self,
        embedding_service,
        llm_service,
        retrieval_service,
        database_service,
    ):
        self.embedding_provider = embedding_service
        self.llm = llm_service
        self.retrieval_service = retrieval_service
        self.database_service = database_service
        self.collection_name = COLLECTION_NAME

    def handle_query(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None,
        top_n: Optional[int] = None,
        cutoff: Optional[float] = None,
        model: str = "ollama",
    ):
        try:
            query_embedding = self.embedding_provider.get_embedding(query)

            top_k = top_k or TOP_K
            top_n = top_n or TOP_N
            cutoff = cutoff or SIMILARITY_CUTOFF

            target_collection = SCHEMA_COLLECTION if is_schema_query(query) else self.collection_name
            print(f"Target collection: {target_collection}")

            chunks = self.retrieval_service.retrieve(
                target_collection,
                query_embedding,
                top_k,
                cutoff,
                filters,
            )
            print(f"Found chunks: {len(chunks)}")

            if not chunks:
                return ChatResponse(
                    answer_text=NO_KB_MSG,
                    sources=[],
                    confidence="low",
                    query_embedding_similarity=[],
                )

            if len(chunks) > top_n:
                chunks = self.retrieval_service.rerank(query, chunks, top_n)
            else:
                chunks = chunks[:top_n]

            is_schema = is_schema_query(query)
            if is_schema:
                sql_query = self.llm.generate_sql_query(chunks, query, model=model)
                print(f"Generated SQL: {sql_query}")
                
                # Safety guardrail
                forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
                sql_upper = sql_query.upper()
                
                if any(kw in sql_upper for kw in forbidden_keywords):
                    db_results = {"error": "Generated SQL contained destructive operations and was blocked."}
                else:
                    db_results = self.database_service.execute_query(sql_query)
                
                print(f"DB Results: {db_results}")
                prompt = self.llm.build_db_grounded_rag_prompt(chunks, db_results, query)
            else:
                prompt = self.llm.build_rag_prompt(chunks, query)

            answer_text = self.llm.generate(prompt, model=model, temperature=0.0, max_tokens=200)

            sources = []
            similarities = []
            for chunk in chunks:
                section_val = chunk.get("section_heading")
                if not section_val:
                    table = chunk.get("table", "")
                    sec = chunk.get("section", "")
                    if table or sec:
                        section_val = f"{table} - {sec}".strip(" -")
                    else:
                        section_val = ""
                        
                sources.append(
                    {
                        "url": chunk.get("url", ""),
                        "title": chunk.get("title", "") or chunk.get("source", ""),
                        "section": section_val,
                        "snippet": chunk.get("text", "")[:300],
                        "char_start": chunk.get("char_start", 0),
                        "char_end": chunk.get("char_end", 0),
                        "score": chunk.get("score", 0.0),
                    }
                )
                similarities.append(chunk.get("score", 0.0))

            avg_similarity = np.mean(similarities) if similarities else 0.0
            if avg_similarity >= 0.8:
                confidence = "high"
            elif avg_similarity >= 0.5:
                confidence = "medium"
            else:
                confidence = "low"

            source_models = [
                Source(
                    url=src["url"] or "https://schema.local/schema_for_vectordb.pdf",
                    title=src["title"] or "Schema PDF",
                    section=src.get("section"),
                    snippet=src.get("snippet", "")[:300],
                    char_start=src.get("char_start", 0),
                    char_end=src.get("char_end", 0),
                    score=min(max(src.get("score", 0.0), 0.0), 1.0),
                )
                for src in sources
            ]

            response = ChatResponse(
                answer_text=answer_text,
                sources=source_models,
                confidence=confidence,
                query_embedding_similarity=similarities,
            )

            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return ChatResponse(
                answer_text=NO_KB_MSG,
                sources=[],
                confidence="low",
                query_embedding_similarity=[],
            )



