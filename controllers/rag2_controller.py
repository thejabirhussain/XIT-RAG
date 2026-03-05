from fastapi import APIRouter, HTTPException, status, Depends

from models.rag2_models import Rag2ChatRequest, Rag2ChatResponse
from handlers.rag2_handlers import Query2Handler
from dependencies import get_query2_handler

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def rag2_health():
    """Quick liveness check for the RAG 2.0 pipeline."""
    return {"status": "ok", "pipeline": "rag2", "version": "POC-0.1"}
