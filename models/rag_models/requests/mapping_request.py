from typing import List
from pydantic import BaseModel, Field

from models.rag_models.field_models import SourceField, TargetGroup


class MappingRequest(BaseModel):
    sources: List[SourceField]
    target_groups: List[TargetGroup]
    min_confidence: float = Field(default=0.45, ge=0.0, le=1.0)
    fuzzy_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    semantic_weight: float = Field(default=0.5, ge=0.0, le=1.0)
