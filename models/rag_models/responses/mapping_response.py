from typing import List
from pydantic import BaseModel

from models.rag_models.field_mapping import TargetMappingResult


class MappingResponse(BaseModel):
    mappings: List[TargetMappingResult]
