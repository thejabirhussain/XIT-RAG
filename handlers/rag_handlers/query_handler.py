from typing import Optional
import time
import logging
import numpy as np
import re

logger = logging.getLogger("query_handler")

from models import ChatResponse, Source
from services.rag_services.retrieval_service import TOP_K, TOP_N, SIMILARITY_CUTOFF

COLLECTION_NAME = "irs_rag_v1"
SCHEMA_COLLECTION = "schema"
NO_KB_MSG = "I don't have verifiable information in the knowledge base for that query."

SCHEMA_KEYWORDS = [
    # Count / aggregation intent
    "how many", "count of", "total number", "number of", "average", "distribution of",
    # Listing intent
    "list all", "show all", "show me all", "give me all", "show me the",
    "fetch all", "get all", "retrieve all", "find policies", "find users",
    # DB-referencing phrases
    "in the db", "in db", "in the database", "from the database",
    "from database", "in our database", "stored in",
    # Schema-specific
    "database schema", "table structure", "column names",
    "foreign key", "data model", "what tables",
    "table columns", "sql query", "db query",
    # Explicit table/record language
    "what records", "which records", "all records",
    "all entries", "all rows", "how many rows", "count of records",
]

# Patterns for specific entities that strongly imply database lookups
DB_ENTITIES = [
    r"policy\s+id\b", r"user\s+id\b", r"org\s+id\b", r"organization\s+id\b", r"risk\s+id\b",
    r"risk\s+score\b", r"\badmin(?:s)\b", r"user\s+roles?\b", r"access\s+level",
    r"draft\s+polic(?:y|ies)\b", r"mitigated\s+risks?\b", r"open\s+risks?\b",
    r"which\s+org(?:anization)?\b", r"which\s+user\b"
]

# Pattern catches natural queries that reference data entities in a question context
SCHEMA_PATTERN = re.compile(
    r"\b(schema|db|audits?|frameworks?|controls?|policies|findings?|users?|organizations?|risks?|orgs?)\b"
    r".*\b(show|list|get|fetch|count|how many|give|find|retrieve|display|what is|are there|who has|which)\b"
    r"|\b(show|list|get|fetch|count|how many|give|find|retrieve|display|what is|are there|who has|which)\b"
    r".*\b(audits?|frameworks?|controls?|policies|findings?|users?|organizations?|risks?|orgs?)\b",
    re.IGNORECASE,
)

MAX_QUERY_LENGTH = 500

def is_schema_query(query: str) -> bool:
    q_lower = query.lower()
    
    # 1. Check strict DB keywords
    if any(keyword in q_lower for keyword in SCHEMA_KEYWORDS):
        return True
        
    # 2. Check for direct entity references like "policy ID 10", "risk score"
    if any(re.search(entity_pattern, q_lower) for entity_pattern in DB_ENTITIES):
        return True
        
    # 3. Check combinations of action words + schema entities
    if SCHEMA_PATTERN.search(q_lower):
        return True
        
    return False

def sanitize_query(query: str) -> str:
    query = query[:MAX_QUERY_LENGTH]
    query = re.sub(
        r"(?i)(ignore previous|forget instructions|system override|"
        r"you are now|disregard all|act as|maintenance mode|developer mode)",
        "[REDACTED]",
        query
    )
    return query.strip()


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
        overall_start = time.perf_counter()
        try:
            t = time.perf_counter()
            query = sanitize_query(query)
            logger.info("[1/7] sanitize_query | query=%s |%.1fms", query, (time.perf_counter() - t) * 1000)

            if not query:
                return ChatResponse(answer_text="The query provided is unclear or empty. Please clarify what you are looking for.", sources=[], confidence="low", query_embedding_similarity=[])
            
            t = time.perf_counter()
            query_embedding = self.embedding_provider.get_embedding(query)
            logger.info("[2/7] get_embedding | %.1fms", (time.perf_counter() - t) * 1000)

            top_k = top_k or TOP_K
            top_n = top_n or TOP_N
            cutoff = cutoff or SIMILARITY_CUTOFF
            is_schema = is_schema_query(query)

            target_collection = SCHEMA_COLLECTION if is_schema_query(query) else self.collection_name
            logger.info("route | collection=%s | schema_path=%s", target_collection, is_schema)
            print(f"Target collection: {target_collection}")


            t = time.perf_counter()
            chunks = self.retrieval_service.retrieve(
                target_collection,
                query_embedding,
                top_k,
                cutoff,
                filters,
            )
            print(f"Found chunks: {len(chunks)}")
            logger.info("[3/7] retrieve | chunks_found=%d | %.1fms", len(chunks), (time.perf_counter() - t) * 1000)

            if not chunks:
                return ChatResponse(
                    answer_text=NO_KB_MSG,
                    sources=[],
                    confidence="low",
                    query_embedding_similarity=[],
                )

            t = time.perf_counter()
            if len(chunks) > top_n:
                chunks = self.retrieval_service.rerank(query, chunks, top_n)
                logger.info("[4/7] rerank | chunks_after=%d | %.1fms", len(chunks), (time.perf_counter() - t) * 1000)
            else:
                chunks = chunks[:top_n]
                logger.info("[4/7] rerank | skipped (chunks <= top_n) | %.1fms", (time.perf_counter() - t) * 1000)

            if is_schema:
                t = time.perf_counter()
                sql_query = self.llm.generate_sql_query(chunks, query, model=model)
                print(f"Generated SQL: {sql_query}")
                logger.info("[5/7] generate_sql | sql_preview=%.100s | %.1fms", sql_query, (time.perf_counter() - t) * 1000)

                
                # Safety guardrail
                forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
                sql_upper = sql_query.strip().upper()
                
                if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
                    logger.warning("[5/7] SQL blocked — did not start with SELECT or WITH")
                    db_results = {"error": "I couldn't safely process this query. Only retrieval queries are permitted."}
                else:
                    t = time.perf_counter()
                    db_results = self.database_service.execute_query(sql_query)
                    row_count = len(db_results.get("results", [])) if "results" in db_results else 0
                    had_error = "error" in db_results
                    logger.info("[6/7] execute_query | rows=%d | error=%s | %.1fms", row_count, had_error, (time.perf_counter() - t) * 1000)

                #if any(kw in sql_upper for kw in forbidden_keywords):
                #    db_results = {"error": "Generated SQL contained destructive operations and was blocked."}
                #else:
                #    db_results = self.database_service.execute_query(sql_query)
                
                print(f"DB Results: {db_results}")
                t = time.perf_counter()
                prompt = self.llm.build_db_grounded_rag_prompt(chunks, db_results, query)
                logger.info("[6/7] build_db_prompt | %.1fms", (time.perf_counter() - t) * 1000)
            else:
                t = time.perf_counter()
                prompt = self.llm.build_rag_prompt(chunks, query)
                logger.info("[5/7] build_rag_prompt | %.1fms", (time.perf_counter() - t) * 1000)

            t = time.perf_counter()
            answer_text = self.llm.generate(prompt, model=model, temperature=0.0, max_tokens=1000)
            logger.info("[7/7] llm_generate | model=%s | answer_len=%d | %.1fms", model, len(answer_text), (time.perf_counter() - t) * 1000)

            source_models = []
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
                        
                raw_score = chunk.get("score", 0.0)
                sim = float(min(max(raw_score, 0.0), 1.0))
                similarities.append(sim)
                
                source_models.append(
                    Source(
                        url=chunk.get("url", "") or "https://schema.local/schema_for_vectordb.pdf",
                        title=chunk.get("title", "") or chunk.get("source", "") or "Schema PDF",
                        section=section_val,
                        snippet=chunk.get("text", "")[:300],
                        char_start=chunk.get("char_start", 0),
                        char_end=chunk.get("char_end", 0),
                        score=sim,
                    )
                )

            avg_similarity = np.mean(similarities) if similarities else 0.0
            if avg_similarity >= 0.8:
                confidence = "high"
            elif avg_similarity >= 0.5:
                confidence = "medium"
            else:
                confidence = "low"

            total_ms = (time.perf_counter() - overall_start) * 1000
            logger.info("✓ handle_query complete | confidence=%s | total=%.1fms", confidence, total_ms)

            response = ChatResponse(
                answer_text=answer_text,
                sources=source_models,
                confidence=confidence,
                query_embedding_similarity=similarities,
            )

            return response

        except Exception as e:
            total_ms = (time.perf_counter() - overall_start) * 1000
            logger.exception("✗ handle_query failed | total=%.1fms | error=%s", total_ms, e)
            import traceback
            traceback.print_exc()
            return ChatResponse(
                answer_text="An unexpected error occurred while processing your request. Please clarify what you're looking for or try again.",
                sources=[],
                confidence="low",
                query_embedding_similarity=[],
            )



