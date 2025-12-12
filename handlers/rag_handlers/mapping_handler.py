"""Handler for field mapping operations."""

import logging
from models import MappingRequest, MappingResponse
from services.rag_services import FieldMappingService

logger = logging.getLogger(__name__)


class MappingHandler:
    """Handler for auto-mapping field operations."""
    
    def __init__(self, mapping_service: FieldMappingService):
        self.mapping_service = mapping_service
        logger.info("MappingHandler initialized")
    
    def handle_mapping(self, request: MappingRequest) -> MappingResponse:
        """
        Handle field mapping request.
        
        Args:
            request: MappingRequest with sources and target groups
            
        Returns:
            MappingResponse with one-to-one field mappings
        """
        logger.info(f"Processing mapping request with {len(request.sources)} sources")
        return self.mapping_service.map_fields(request)
