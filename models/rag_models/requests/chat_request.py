from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    query: str = Field(..., description="User query", min_length=1, max_length=2000)
    chat_history: Optional[list[dict[str, str]]] = Field(
        None, description="Conversational history for follow-up context"
    )
    filters: Optional[dict[str, Any]] = Field(
        None, description="Optional filters for retrieval"
    )
    json: bool = Field(False, description="Return JSON response format")
    model: str = Field("ollama", description="Model selection: 'ollama' or 'gemini'")
