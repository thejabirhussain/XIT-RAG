from typing import Optional
from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    source_id: str
    source_name: str
    source_datatype: str
    confidence: float = Field(ge=0.0, le=1.0)
    transform: Optional[str] = None


class TargetMappingResult(BaseModel):
    id: str
    name: str
    description: Optional[str]
    datatype: str
    required: bool
    mapping: Optional[FieldMapping]
