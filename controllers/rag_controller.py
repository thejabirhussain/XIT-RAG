import os
import logging

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Security
from fastapi.security.api_key import APIKeyHeader

from models import ChatRequest, ChatResponse, AdminStats, IngestionRequest
from handlers import QueryHandler, IngestionHandler, StatsHandler
from dependencies import get_query_handler, get_ingestion_handler, get_stats_handler

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query(
    request: ChatRequest,
    handler: QueryHandler = Depends(get_query_handler)
):
    try:
        return handler.handle_query(query=request.query, filters=request.filters, model=request.model)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/stats", response_model=AdminStats)
async def get_stats(handler: StatsHandler = Depends(get_stats_handler)):
    try:
        return handler.handle_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def _run_ingestion(handler: IngestionHandler, request: IngestionRequest):
    """Wrapper function to run ingestion in background"""
    try:
        return handler.handle_ingestion(request)
    except Exception as e:
        # Log error but don't raise - background task
        print(f"Ingestion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@router.post("/ingest")
async def trigger_ingest(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    handler: IngestionHandler = Depends(get_ingestion_handler)
):
    try:
        # Add ingestion task to background - FastAPI will run it after response is sent
        background_tasks.add_task(_run_ingestion, handler, request)
        
        # Return immediately with acceptance message
        return {
            "status": "accepted",
            "message": "Ingestion started in background",
            "seed_url": request.seed_url,
            "max_pages": request.max_pages,
            "concurrency": request.concurrency,
            "note": "Ingestion is processing. Check /stats endpoint for progress."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
