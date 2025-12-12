from typing import List, Optional
from pydantic import BaseModel, Field


class LocalAccount(BaseModel):
    """Local GL account to be mapped"""
    Code: str
    Description: str
    ExpectedType: Optional[str] = ""
    ERP: Optional[str] = ""


class SystemCOAAccount(BaseModel):
    """System Chart of Accounts entry"""
    Id: str
    Name: str
    Category: Optional[str] = ""


class ERPMappingRequest(BaseModel):
    """Request for ERP account mapping"""
    localAccounts: List[LocalAccount]
    systemCOA: List[SystemCOAAccount]
    auto_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
