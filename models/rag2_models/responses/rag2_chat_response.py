from pydantic import BaseModel
from typing import Optional, List, Any


class SqlResult(BaseModel):
    generated_sql: str
    row_count: int
    rows: List[dict[str, Any]]


class VectorSource(BaseModel):
    score: float
    title: str
    text: str
    url: Optional[str] = None
    section_heading: Optional[str] = None


class Rag2ChatResponse(BaseModel):
    query: str
    org_id: int
    route: str              # "structured" | "knowledge" | "hybrid"
    confidence: float
    answer: str
    sql_result: Optional[SqlResult] = None
    vector_sources: Optional[List[VectorSource]] = None
    error: Optional[str] = None
