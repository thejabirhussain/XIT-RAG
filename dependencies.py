import os
from functools import lru_cache
from dotenv import load_dotenv

from services import EmbeddingService, LLMService, QdrantService, RetrievalService, IngestionService
from handlers import QueryHandler, IngestionHandler, StatsHandler

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Handlers

@lru_cache()
def get_query_handler() -> QueryHandler:
    return QueryHandler(
        embedding_service=get_embedding_service(),
        llm_service=get_llm_service(),
        retrieval_service=get_retrieval_service(),
    )

@lru_cache()
def get_ingestion_handler() -> IngestionHandler:
    return IngestionHandler(
        embedding_service=get_embedding_service(),
        qdrant_service=get_qdrant_service(),
        ingestion_service=get_ingestion_service(),
    )

@lru_cache()
def get_stats_handler() -> StatsHandler:
    return StatsHandler(qdrant_service=get_qdrant_service())

# Services

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService(ollama_host=OLLAMA_HOST, gemini_api_key=GEMINI_API_KEY)

@lru_cache()
def get_qdrant_service() -> QdrantService:
    return QdrantService(url=QDRANT_URL, api_key=QDRANT_API_KEY)

@lru_cache()
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(get_qdrant_service())

@lru_cache()
def get_ingestion_service() -> IngestionService:
    return IngestionService(vector_db_service=get_qdrant_service())


# ── RAG 2.0 Dependencies ─────────────────────────────────────────────────

from services.rag2_services import RouterService, MSSQLService, Text2SQLService, LLM2Service
from handlers.rag2_handlers import Query2Handler

MSSQL_CONNECTION_STRING = os.getenv("MSSQL_CONNECTION_STRING", "")
TEXT2SQL_MODEL = os.getenv("TEXT2SQL_MODEL", "llama3.1:8b")  # swap to arctic when ready

@lru_cache()
def get_router_service() -> RouterService:
    return RouterService(ollama_host=OLLAMA_HOST)

@lru_cache()
def get_mssql_service() -> MSSQLService:
    return MSSQLService(connection_string=MSSQL_CONNECTION_STRING)

@lru_cache()
def get_text2sql_service() -> Text2SQLService:
    return Text2SQLService(ollama_host=OLLAMA_HOST, model=TEXT2SQL_MODEL)

@lru_cache()
def get_llm2_service() -> LLM2Service:
    return LLM2Service(ollama_host=OLLAMA_HOST, gemini_api_key=GEMINI_API_KEY)

@lru_cache()
def get_query2_handler() -> Query2Handler:
    return Query2Handler(
        router_service=get_router_service(),
        text2sql_service=get_text2sql_service(),
        mssql_service=get_mssql_service(),
        llm2_service=get_llm2_service(),
        embedding_service=get_embedding_service(),   # reuse existing
        retrieval_service=get_retrieval_service(),   # reuse existing
    )
