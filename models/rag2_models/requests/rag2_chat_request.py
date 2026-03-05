from pydantic import BaseModel, Field
from typing import Optional, Literal


class Rag2ChatRequest(BaseModel):
    query: str = Field(..., description="Natural language question about compliance data")
    org_id: int = Field(..., description="Tenant org_id — all SQL queries are scoped to this")
    model: Literal["gemini", "ollama"] = Field(
        default="gemini",
        description="LLM backend for final answer generation"
    )
    force_route: Optional[Literal["structured", "knowledge", "hybrid"]] = Field(
        default=None,
        description="Override router classification (useful for testing)"
    )
    top_k_docs: int = Field(default=5, description="Top-K chunks to retrieve for knowledge path")
