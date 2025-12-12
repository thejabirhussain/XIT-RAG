#controllers/rag_controller.py
from fastapi import APIRouter, HTTPException, status, Depends

from models import ChatRequest, ChatResponse, AdminStats, IngestionRequest, MappingRequest, MappingResponse 
from handlers import QueryHandler, IngestionHandler, StatsHandler, MappingHandler
from dependencies import get_query_handler, get_ingestion_handler, get_stats_handler, get_mapping_handler

from models import ERPMappingRequest, ERPMappingResponse  # Add to imports
from handlers import ERPMappingHandler  # Add to imports
from dependencies import get_erp_mapping_handler  # Add to imports
router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query(
    request: ChatRequest,
    handler: QueryHandler = Depends(get_query_handler)
):
    try:
        return handler.handle_query(query=request.query, filters=request.filters)
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


@router.post("/ingest")
async def trigger_ingest(
    request: IngestionRequest,
    handler: IngestionHandler = Depends(get_ingestion_handler)
):
    try:
        return handler.handle_ingestion(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/auto-map", response_model=MappingResponse)
async def auto_map(
    request: MappingRequest,
    handler: MappingHandler = Depends(get_mapping_handler)
):
    """
    Auto-map source fields to target fields using hybrid fuzzy + semantic matching.
    """
    try:
        return handler.handle_mapping(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/erp-map", response_model=ERPMappingResponse)
async def erp_map(
    request: ERPMappingRequest,
    handler: ERPMappingHandler = Depends(get_erp_mapping_handler)
):
    """
    Map GL accounts to Chart of Accounts using hybrid semantic + fuzzy matching.
    """
    try:
        return handler.handle_mapping(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )