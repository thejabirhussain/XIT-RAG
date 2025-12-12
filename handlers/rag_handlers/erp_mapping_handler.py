"""Handler for ERP account mapping operations."""

import logging
from models import ERPMappingRequest, ERPMappingResponse
from services.rag_services import ERPMappingService

logger = logging.getLogger(__name__)


class ERPMappingHandler:
    """Handler for ERP account to COA mapping operations."""
    
    def __init__(self, mapping_service: ERPMappingService):
        self.mapping_service = mapping_service
        logger.info("ERPMappingHandler initialized")
    
    def handle_mapping(self, request: ERPMappingRequest) -> ERPMappingResponse:
        """
        Handle ERP account mapping request.
        
        Args:
            request: ERPMappingRequest with local accounts and system COA
            
        Returns:
            ERPMappingResponse with mapping results
        """
        logger.info(f"Processing ERP mapping: {len(request.localAccounts)} accounts")
        return self.mapping_service.map_accounts(request)
