from typing import Literal, Optional
from pydantic import BaseModel, Field
from models.rag_models.responses.source import Source


class ChatResponse(BaseModel):


    answer_text: str
    sources: list[Source]
    confidence: Literal["low", "medium", "high"]
    query_embedding_similarity: list[float] = Field(
        ..., description="Similarity scores for retrieved chunks"
    )
    generated_sql: Optional[str] = Field(None, description="The SQL statement generated, if any")
    active_collection: Optional[str] = Field(None, description="The schema or collection being accessed/activated")
