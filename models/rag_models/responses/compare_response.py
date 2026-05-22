from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from models.rag_models.responses.source import Source


class CompareModelResponse(BaseModel):
    answer_text: str
    sources: list[Source]
    confidence: Literal["low", "medium", "high"]
    query_embedding_similarity: list[float] = Field(
        ..., description="Similarity scores for retrieved chunks"
    )
    generated_sql: Optional[str] = Field(None, description="The SQL statement generated, if any")
    active_collection: Optional[str] = Field(None, description="The schema or collection being accessed/activated")
    db_results: Optional[list[dict]] = Field(None, description="Raw database query results when record count is below threshold")
    total_records: Optional[int] = Field(None, description="Total number of records returned by the database query")
    export_id: Optional[str] = Field(None, description="ID to download CSV via /export/{export_id} when record count exceeds threshold")
    
    # Compare metadata
    model_name: str = Field(..., description="Display name of the model")
    elapsed_ms: float = Field(..., description="Generation time in milliseconds")
    token_usage: Optional[dict[str, Any]] = Field(None, description="Token usage statistics")
    prompt_sent: Optional[str] = Field(None, description="The full prompt sent to the model")
    logs: Optional[str] = Field(None, description="Execution and SQL traces for this model")


class CompareResponse(BaseModel):
    query: str
    responses: dict[str, CompareModelResponse]
