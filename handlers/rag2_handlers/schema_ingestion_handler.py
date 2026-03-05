import logging
from services.rag2_services import SchemaIngestionService
from models.rag2_models.responses.schema_ingest_response import SchemaIngestResponse

logger = logging.getLogger(__name__)


class SchemaIngestionHandler:
    def __init__(self, schema_ingestion_service: SchemaIngestionService):
        self.service = schema_ingestion_service

    def handle_from_upload(
        self,
        pdf_bytes: bytes,
        collection_name: str = "compliance_schema",
        recreate_collection: bool = False,
    ) -> SchemaIngestResponse:
        logger.info(f"[SchemaIngestionHandler] Starting ingestion → collection: {collection_name}")
        result = self.service.ingest_from_bytes(
            pdf_bytes=pdf_bytes,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )
        return SchemaIngestResponse(**result)

    def handle_from_path(
        self,
        pdf_path: str,
        collection_name: str = "compliance_schema",
        recreate_collection: bool = False,
    ) -> SchemaIngestResponse:
        logger.info(f"[SchemaIngestionHandler] Ingesting from path: {pdf_path}")
        result = self.service.ingest_from_path(
            pdf_path=pdf_path,
            collection_name=collection_name,
            recreate_collection=recreate_collection,
        )
        return SchemaIngestResponse(**result)
