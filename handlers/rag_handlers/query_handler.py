from typing import Optional
import time
import logging
import numpy as np
import re
import uuid
import httpx

logger = logging.getLogger("query_handler")

from models import ChatResponse, Source
from services.rag_services.retrieval_service import TOP_K, TOP_N, SIMILARITY_CUTOFF

COLLECTION_NAME = "irs_rag_v1"
SCHEMA_COLLECTION = "schema"
NO_KB_MSG = "I don't have verifiable information in the knowledge base for that query."

# ──────────────────────────────────────────────────────────────
# ERD CONTEXT MAP  —  built from your database ERD
# Update this whenever tables/columns change. This is the single
# source of truth for schema routing.
# ──────────────────────────────────────────────────────────────
ERD_CONTEXT_MAP = {
    "policies": {
        "aliases": ["policy", "policies"],
        "columns": ["policy_id", "policy_name", "policy_status", "draft", "published", "archived"],
        "terms":   ["compliance policy", "security policy", "policy document"],
    },
    "users": {
        "aliases": ["user", "users", "member", "members", "admin", "admins"],
        "columns": ["user_id", "username", "email", "role", "access level"],
        "terms":   ["superuser", "who has access", "account holder"],
    },
    "organizations": {
        "aliases": ["org", "orgs", "organization", "organizations", "company", "tenant"],
        "columns": ["org_id", "org_name"],
        "terms":   ["which org", "which organization", "belongs to"],
    },
    "risks": {
        "aliases": ["risk", "risks", "threat", "threats", "vulnerability"],
        "columns": ["risk_id", "risk_score", "risk_status", "likelihood", "impact"],
        "terms":   ["mitigated risk", "open risk", "risk level", "residual risk"],
    },
    "audits": {
        "aliases": ["audit", "audits"],
        "columns": ["audit_id", "audit_date", "audit_status", "auditor"],
        "terms":   ["audit trail", "audit log", "audit result"],
    },
    "frameworks": {
        "aliases": ["framework", "frameworks", "standard", "standards"],
        "columns": ["framework_id", "framework_name"],
        "terms":   ["gdpr", "iso 27001", "soc 2", "nist", "pci dss", "hipaa"],
    },
    "controls": {
        "aliases": ["control", "controls"],
        "columns": ["control_id", "control_name", "control_status"],
        "terms":   ["control objective", "control item", "control mapping"],
    },
    "findings": {
        "aliases": ["finding", "findings", "observation", "observations"],
        "columns": ["finding_id", "finding_status", "finding_type"],
        "terms":   ["non-conformity", "gap", "issue"],
    },
}

# Explicit DB-reference phrases — still supported for power users / backward compat
EXPLICIT_DB_KEYWORDS = [
    "in the db", "in db", "in the database", "from the database",
    "from database", "in our database", "stored in",
    "sql query", "db query", "database schema", "table structure",
    "column names", "foreign key", "data model", "what tables",
]

# Patterns for specific DB entity references (e.g. "policy ID 10", "risk score")
DB_ENTITIES = [
    r"policy\s+id\b", r"user\s+id\b", r"org\s+id\b", r"organization\s+id\b", r"risk\s+id\b",
    r"risk\s+score\b", r"user\s+roles?\b", r"access\s+level",
    r"draft\s+polic(?:y|ies)\b", r"mitigated\s+risks?\b", r"open\s+risks?\b",
]

# Data-retrieval intent patterns — "I want records", not "I want to understand"
DATA_RETRIEVAL_INTENTS = [
    r"\b(show|list|display|fetch|get|retrieve|give me|find|pull)\b",
    r"\b(how many|count|total number of|number of|average|distribution of)\b",
    r"\b(what is the|what are the|what's the|whats the)\b.{0,40}\b(status|score|level|value|name|id|date|number|count)\b",
    r"\b(which|who|whose)\b.{0,40}\b(has|have|is|are|with|belongs|assigned|linked)\b",
    r"\b(are there|is there|do we have|does .{1,30} exist)\b",
    r"\b(details? of|info(?:rmation)? (?:on|about|for))\b",
    r"\b(all|every|each)\b.{0,30}\b(record|entry|row|item|result)s?\b",
]

MAX_QUERY_LENGTH = 500

# ──────────────────────────────────────────────────────────────
# SEMANTIC ROUTER
# Uses cosine similarity between the query embedding and
# pre-computed intent centroids to classify schema vs IRS route.
# ──────────────────────────────────────────────────────────────

SCHEMA_INTENT_SEEDS = [
    "list all users in the system",
    "show me all risks",
    "how many policies are published",
    "count the number of audits",
    "which organizations exist",
    "get all controls with active status",
    "fetch all findings for this org",
    "what is the risk score",
    "show all frameworks",
    "retrieve records from the database",
    "display all entries in the table",
    "total number of open risks",
    "who are the admins",
    "how many mitigated risks do we have",
]

IRS_INTENT_SEEDS = [
    "what is the standard deduction",
    "how do I file my taxes",
    "what are the requirements for claiming a deduction",
    "explain the rules for tax exemptions",
    "what does the IRS say about",
    "how to report income on my return",
    "what is the deadline for tax filing",
    "can I deduct home office expenses",
    "what are the penalties for late filing",
    "how does the earned income credit work",
    "what forms do I need to submit to the IRS",
    "explain IRS publication guidelines",
]

# Schema must beat IRS by this margin to trigger schema route.
# Lower = more aggressive schema routing; raise if over-routing to DB.
SEMANTIC_SCHEMA_MARGIN = 0.12


class SemanticRouter:
    """
    Classifies a pre-computed query embedding as 'schema' or 'irs'
    using cosine similarity against intent centroids.
    Centroids are built lazily on first use and then cached.
    """

    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self._schema_centroid: np.ndarray | None = None
        self._irs_centroid: np.ndarray | None = None

    def warm_up(self):
        """Call once at startup to pre-build centroids (avoids first-query latency)."""
        self._build_centroids()

    def _build_centroids(self):
        logger.info("SemanticRouter | building intent centroids ...")
        schema_vecs = [
            np.array(self.embedding_service.get_embedding(s))
            for s in SCHEMA_INTENT_SEEDS
        ]
        irs_vecs = [
            np.array(self.embedding_service.get_embedding(s))
            for s in IRS_INTENT_SEEDS
        ]
        self._schema_centroid = np.mean(schema_vecs, axis=0)
        self._irs_centroid    = np.mean(irs_vecs,    axis=0)
        logger.info("SemanticRouter | centroids ready.")

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom else 0.0

    def classify(
        self, query_embedding: list | np.ndarray
    ) -> tuple[str, float, float]:
        """
        Returns (route, schema_score, irs_score).
        route is 'schema' or 'irs'.
        """
        if self._schema_centroid is None:
            self._build_centroids()

        qvec = np.array(query_embedding)
        schema_score = self._cosine(qvec, self._schema_centroid)
        irs_score    = self._cosine(qvec, self._irs_centroid)

        logger.debug(
            "SemanticRouter | schema_score=%.4f | irs_score=%.4f | margin=%.4f",
            schema_score, irs_score, schema_score - irs_score,
        )

        route = "schema" if (schema_score - irs_score) >= SEMANTIC_SCHEMA_MARGIN else "irs"
        return route, schema_score, irs_score


def _extract_erd_entities(query: str) -> list:
    """Return table names from ERD whose aliases/columns/terms appear in the query."""
    q_lower = query.lower()
    matched = []
    for table, ctx in ERD_CONTEXT_MAP.items():
        all_terms = ctx["aliases"] + ctx["columns"] + ctx["terms"]
        if any(term in q_lower for term in all_terms):
            matched.append(table)
    return matched


def _has_data_retrieval_intent(query: str) -> bool:
    """Return True if the query is asking to fetch/count/look up data records."""
    q_lower = query.lower()
    return any(re.search(pattern, q_lower, re.IGNORECASE) for pattern in DATA_RETRIEVAL_INTENTS)


def is_schema_query(query: str) -> bool:
    q_lower = query.lower()

    # 1. Explicit DB references — always schema (backward compat + power users)
    if any(kw in q_lower for kw in EXPLICIT_DB_KEYWORDS):
        return True

    # 2. Specific entity ID/score patterns — always schema
    if any(re.search(p, q_lower) for p in DB_ENTITIES):
        return True

    # 3. ERD context map: entity match + data-retrieval intent — both required
    #    This handles natural language without any DB-specific keywords
    matched_entities = _extract_erd_entities(query)
    if matched_entities and _has_data_retrieval_intent(query):
        logger.debug("schema route via ERD | tables=%s", matched_entities)
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
        self.semantic_router = SemanticRouter(embedding_service)


    def handle_query(
        self,
        query: str,
        chat_history: Optional[list[dict[str, str]]] = None,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None,
        top_n: Optional[int] = None,
        cutoff: Optional[float] = None,
        model: str = "ollama",
    ):
        overall_start = time.perf_counter()
        request_id = uuid.uuid4().hex[:6]

        try:
            t = time.perf_counter()
            query = sanitize_query(query)
            logger.info("[%s] [1/8] sanitize_query | query=%s |%.1fms", request_id, query, (time.perf_counter() - t) * 1000)

            if not query:
                return ChatResponse(answer_text="The query provided is unclear or empty. Please clarify what you are looking for.", sources=[], confidence="low", query_embedding_similarity=[], generated_sql=None, active_collection=None)
            
            # Step 0: Rewrite Query based on chat history
            if chat_history:
                t = time.perf_counter()
                query = self.llm.rewrite_query(chat_history, query, model=model)
                logger.info("[%s] [1.5/8] rewrite_query | new_query=%s | %.1fms", request_id, query, (time.perf_counter() - t) * 1000)

            t = time.perf_counter()
            query_embedding = self.embedding_provider.get_embedding(query)
            logger.info("[%s] [2/8] get_embedding | %.1fms", request_id, (time.perf_counter() - t) * 1000)

            top_k = top_k or TOP_K
            top_n = top_n or TOP_N
            cutoff = cutoff or SIMILARITY_CUTOFF
            is_schema = is_schema_query(query)
            
            if not is_schema:           
                sem_route, schema_score, irs_score = self.semantic_router.classify(query_embedding)
                is_schema = (sem_route == "schema")
                logger.info(
                    "[%s] semantic_route | route=%s | schema_score=%.4f | irs_score=%.4f",
                    request_id, sem_route, schema_score, irs_score,
                )
            else:
                logger.info("[%s] keyword_route | schema=True (keyword/regex match)", request_id)
            
            target_collection = SCHEMA_COLLECTION if is_schema else self.collection_name
            logger.info("[%s] route | collection=%s | is_schema=%s", request_id, target_collection, is_schema)
            print(f"[{request_id}] Target collection: {target_collection}")

            t = time.perf_counter()
            chunks = self.retrieval_service.retrieve(
                target_collection,
                query_embedding,
                top_k,
                cutoff,
                filters,
            )
            print(f"[{request_id}] Found chunks: {len(chunks)}")
            logger.info("[%s] [3/8] retrieve | chunks_found=%d | %.1fms", request_id, len(chunks), (time.perf_counter() - t) * 1000)

            if not chunks:
                return ChatResponse(
                    answer_text=NO_KB_MSG,
                    sources=[],
                    confidence="low",
                    query_embedding_similarity=[],
                    generated_sql=None,
                    active_collection=target_collection,
                )

            t = time.perf_counter()
            if len(chunks) > top_n:
                chunks = self.retrieval_service.rerank(query, chunks, top_n)
                logger.info("[%s] [4/8] rerank | chunks_after=%d | %.1fms", request_id, len(chunks), (time.perf_counter() - t) * 1000)
            else:
                chunks = chunks[:top_n]
                logger.info("[%s] [4/8] rerank | skipped (chunks <= top_n) | %.1fms", request_id, (time.perf_counter() - t) * 1000)

            if is_schema:
                t = time.perf_counter()
                sql_query = self.llm.generate_sql_query(chunks, query, model=model)
                print(f"[{request_id}] Generated SQL: {sql_query}")
                logger.info("[%s] [5/8] generate_sql | sql_preview=%.100s | %.1fms", request_id, sql_query, (time.perf_counter() - t) * 1000)
                
                # Safety guardrail
                sql_upper = sql_query.strip().upper()
                if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
                    logger.warning("[%s] [5/8] SQL blocked — did not start with SELECT or WITH", request_id)
                    db_results = {"error": "I couldn't safely process this query. Only retrieval queries are permitted."}
                else:
                    t = time.perf_counter()
                    db_results = self.database_service.execute_query(sql_query)
                    row_count = len(db_results.get("results", [])) if "results" in db_results else 0
                    had_error = "error" in db_results
                    logger.info("[%s] [6/8] execute_query | rows=%d | error=%s | %.1fms", request_id, row_count, had_error, (time.perf_counter() - t) * 1000)
                
                print(f"[{request_id}] DB Results: {db_results}")
                t = time.perf_counter()
                prompt = self.llm.build_db_grounded_rag_prompt(chunks, db_results, query)
                logger.info("[%s] [7/8] build_db_prompt | %.1fms", request_id, (time.perf_counter() - t) * 1000)
            else:
                t = time.perf_counter()
                prompt = self.llm.build_rag_prompt(chunks, query)
                logger.info("[%s] [7/8] build_rag_prompt | %.1fms", request_id, (time.perf_counter() - t) * 1000)

            t = time.perf_counter()
            answer_text = self.llm.generate(prompt, model=model, temperature=0.0, max_tokens=1000)
            logger.info("[%s] [8/8] llm_generate | model=%s | answer_len=%d | %.1fms", request_id, model, len(answer_text), (time.perf_counter() - t) * 1000)

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
            logger.info("[%s] ✓ handle_query complete | confidence=%s | total=%.1fms", request_id, confidence, total_ms)

            response = ChatResponse(
                answer_text=answer_text,
                sources=source_models,
                confidence=confidence,
                query_embedding_similarity=similarities,
                generated_sql=sql_query if is_schema else None,
                active_collection=target_collection,
            )

            return response
            
        except httpx.RequestError as e:
            total_ms = (time.perf_counter() - overall_start) * 1000
            logger.exception("[%s] ✗ handle_query failed (LLM Network Error) | total=%.1fms | error=%s", request_id, total_ms, e)
            return ChatResponse(
                answer_text="I am currently experiencing network delays connecting to the language model. Please try again in an moment.",
                sources=[],
                confidence="low",
                query_embedding_similarity=[],
                generated_sql=None,
                active_collection=None,
            )
            
        except httpx.HTTPStatusError as e:
            total_ms = (time.perf_counter() - overall_start) * 1000
            logger.exception("[%s] ✗ handle_query failed (LLM Endpoint Error) | total=%.1fms | error=%s", request_id, total_ms, e)
            return ChatResponse(
                answer_text="The language model returned an error while processing your request. It may be overloaded. Please try again or simplify your query.",
                sources=[],
                confidence="low",
                query_embedding_similarity=[],
                generated_sql=None,
                active_collection=None,
            )

        except Exception as e:
            total_ms = (time.perf_counter() - overall_start) * 1000
            logger.exception("[%s] ✗ handle_query failed (Unknown Error) | total=%.1fms | error=%s", request_id, total_ms, e)
            import traceback
            traceback.print_exc()
            return ChatResponse(
                answer_text="An unexpected error occurred while processing your request. Please clarify what you're looking for or try again.",
                sources=[],
                confidence="low",
                query_embedding_similarity=[],
                generated_sql=None,
                active_collection=None,
            )



