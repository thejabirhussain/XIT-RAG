from pydantic import BaseModel
from typing import List


class SchemaIngestResponse(BaseModel):
    status: str
    collection_name: str
    chunks_stored: int
    vector_size: int
    tables_parsed: List[str]
    message: str = ""
