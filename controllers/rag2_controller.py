from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form

from models.rag2_models import Rag2ChatRequest, Rag2ChatResponse
from handlers.rag2_handlers import Query2Handler, SchemaIngestionHandler
from dependencies import get_query2_handler, get_schema_ingestion_handler
from models.rag2_models.responses.schema_ingest_response import SchemaIngestResponse
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag2", tags=["RAG 2.0 — Compliance SQL+Vector"])


@router.post("/query", response_model=Rag2ChatResponse)
async def rag2_query(
    request: Rag2ChatRequest,
    handler: Query2Handler = Depends(get_query2_handler),
):
    """
    Dual-pipeline RAG endpoint.
    Routes to SQL (structured), vector (knowledge), or both (hybrid)
    based on query intent classification.
    """
    try:
        return handler.handle_query(
            query=request.query,
            org_id=request.org_id,
            model=request.model,
            force_route=request.force_route,
            top_k_docs=request.top_k_docs,
        )
    except Exception as e:
        logger.error(f"[rag2_query] FAILED: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())   # ← full traceback in terminal
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def rag2_health():
    """Quick liveness check for the RAG 2.0 pipeline."""
    return {"status": "ok", "pipeline": "rag2", "version": "POC-0.1"}

@router.post("/ingest/schema/upload", response_model=SchemaIngestResponse)
async def ingest_schema_upload(
    file: UploadFile = File(..., description="schema_for_vectordb.pdf"),
    collection_name: str = Form(default="compliance_schema"),
    recreate_collection: bool = Form(default=False),
    handler: SchemaIngestionHandler = Depends(get_schema_ingestion_handler),
):
    """
    Upload the schema PDF and ingest it into a dedicated Qdrant collection.
    Use recreate_collection=true to wipe and re-ingest cleanly.
    """
    try:
        pdf_bytes = await file.read()
        return handler.handle_from_upload(
            pdf_bytes=pdf_bytes,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/schema/path", response_model=SchemaIngestResponse)
async def ingest_schema_from_path(
    pdf_path: str,
    collection_name: str = "compliance_schema",
    recreate_collection: bool = False,
    handler: SchemaIngestionHandler = Depends(get_schema_ingestion_handler),
):
    """
    Ingest schema PDF from a local server file path.
    Useful when the PDF is already on the server filesystem.
    """
    try:
        return handler.handle_from_path(
            pdf_path=pdf_path,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))