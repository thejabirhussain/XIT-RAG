"""Models package - Data structures."""

from .rag_models import (
    Chunk,
    ChunkMetadata,
    ContentType,
    CrawledPage,
    VectorChunk,
    ChatRequest,
    IngestionRequest,
    ReindexRequest,
    ChatResponse,
    AdminStats,
    Source,
)
from .rag2_models import (
    Rag2ChatRequest,
    Rag2ChatResponse,
    SqlResult,
    VectorSource,
    SchemaIngestResponse,
)

__all__ = [
    "Chunk",
    "ChunkMetadata",
    "ContentType",
    "CrawledPage",
    "VectorChunk",
    "ChatRequest",
    "IngestionRequest",
    "ReindexRequest",
    "ChatResponse",
    "AdminStats",
    "Source",
    "Rag2ChatRequest",
    "Rag2ChatResponse",
    "SqlResult",
    "VectorSource",
    "SchemaIngestResponse",
]

