from typing import List, Optional
from pydantic import BaseModel


class SourceField(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    datatype: str = "string"


class TargetField(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    datatype: str = "string"
    required: bool = False


class TargetGroup(BaseModel):
    name: str
    fields: List[TargetField]
