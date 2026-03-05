import os
import logging
import traceback
from services.rag2_services import RouterService, MSSQLService, Text2SQLService, LLM2Service
from models.rag2_models import Rag2ChatResponse, SqlResult, VectorSource

logger = logging.getLogger(__name__)

HYBRID_CONFIDENCE_THRESHOLD = 0.80
COMPLIANCE_COLLECTION        = os.getenv("COMPLIANCE_COLLECTION", "compliance_docs")
COMPLIANCE_SCHEMA_COLLECTION = os.getenv("COMPLIANCE_SCHEMA_COLLECTION", "compliance_schema")


class Query2Handler:
    def __init__(
        self,
        router_service: RouterService,
        text2sql_service: Text2SQLService,
        mssql_service: MSSQLService,
        llm2_service: LLM2Service,
        embedding_service,
        retrieval_service,
    ):
        self.router    = router_service
        self.text2sql  = text2sql_service
        self.mssql     = mssql_service
        self.llm2      = llm2_service
        self.embedder  = embedding_service
        self.retrieval = retrieval_service

    def handle_query(
        self,
        query: str,
        org_id: int,
        model: str = "ollama",
        force_route: str | None = None,
        top_k_docs: int = 5,
    ) -> Rag2ChatResponse:

        # ── Step 1: Route ──────────────────────────────────────────────────────
        if force_route:
            route, confidence = force_route, 1.0
        else:
            route, confidence = self.router.classify(query)
            if confidence < HYBRID_CONFIDENCE_THRESHOLD and route != "hybrid":
                route = "hybrid"

        logger.info(f"[Query2Handler] route={route} confidence={confidence} org_id={org_id}")

        sql_result:     SqlResult | None      = None
        vector_sources: list[VectorSource]    = []
        context_parts:  list[str]             = []
        error_detail:   str | None            = None

        # ── Step 2a: SQL Path ──────────────────────────────────────────────────
        if route in ("structured", "hybrid"):

            # 2a-i: Retrieve relevant schema chunks from Qdrant
            logger.info(f"[Query2Handler] Retrieving schema chunks from '{COMPLIANCE_SCHEMA_COLLECTION}'")
            schema_vec    = self.embedder.get_embedding(query)
            schema_chunks = self.retrieval.retrieve(
                collection=COMPLIANCE_SCHEMA_COLLECTION,
                query_vec=schema_vec,
                top_k=2,
                cutoff=0.15,
            )
            schema_context = "\n\n".join(c["text"] for c in schema_chunks)
            logger.info(f"[Query2Handler] Schema chunks retrieved: {len(schema_chunks)}")

            # 2a-ii: Generate SQL
            logger.info(f"[Query2Handler] Calling Text2SQL model: {self.text2sql.model}")
            sql = self.text2sql.generate_sql(query, org_id, schema_context)
            logger.info(f"[Query2Handler] Generated SQL: {sql}")

            # 2a-iii: Execute against MySQL
            logger.info(f"[Query2Handler] Executing SQL against MySQL")
            rows = self.mssql.execute_query(sql)
            logger.info(f"[Query2Handler] MySQL returned {len(rows)} rows")

            sql_result = SqlResult(
                generated_sql=sql,
                row_count=len(rows),
                rows=rows,
            )
            context_parts.append(self.llm2.format_sql_context(sql, rows))

        # ── Step 2b: Vector Path ───────────────────────────────────────────────
        if route in ("knowledge", "hybrid"):
            logger.info(f"[Query2Handler] Retrieving knowledge chunks from '{COMPLIANCE_COLLECTION}'")
            query_vec = self.embedder.get_embedding(query)
            chunks    = self.retrieval.retrieve(
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
                context_parts.append(self.llm2.format_vector_context(reranked))
                logger.info(f"[Query2Handler] Vector path returned {len(reranked)} chunks")

        # ── Step 3: Final Answer ───────────────────────────────────────────────
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
            error=error_detail,
        )
