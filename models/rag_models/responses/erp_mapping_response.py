from typing import List, Optional
from pydantic import BaseModel, Field  # Add Field import


class ERPMappingResult(BaseModel):
    """Single account mapping result"""
    ERP: str
    Code: str
    Extracted: Optional[str]
    MappedCOAID: Optional[str] = Field(alias="Mapped COA ID")
    COAName: str = Field(alias="COA Name")
    COADescription: str = Field(alias="COA Description")
    Type: str
    Score: float
    NeedsReview: str = Field(alias="Needs Review")
    DescriptionProvided: str
    ExpectedType: str
    TypeMismatch: str
    
    class Config:
        populate_by_name = True


class ERPMappingResponse(BaseModel):
    """Response for ERP account mapping"""
    ProcessedAt: str
    TotalRecords: int
    SuccessfulMappings: int
    RequireReview: int
    MappingResult: List[ERPMappingResult]
    ProcessingTimeMs: Optional[float] = None
