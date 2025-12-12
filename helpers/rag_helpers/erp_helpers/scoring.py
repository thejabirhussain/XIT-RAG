"""Scoring utilities for ERP account mapping."""

from functools import lru_cache
from typing import Optional
from .normalization import extract_natural_account, normalize_type


@lru_cache(maxsize=1024)
def code_quality(local_code: str, type_hint: Optional[str] = None, 
                 system_type: Optional[str] = None) -> float:
    """Calculate quality score for extracted natural account code."""
    score = 0.0
    nat = extract_natural_account(local_code or "")
    
    if nat:
        score += 0.3
        if 3 <= len(nat) <= 6:
            score += 0.2
    
    if normalize_type(type_hint or "") == normalize_type(system_type or ""):
        score += 0.2
    
    return min(score, 1.0)


@lru_cache(maxsize=1024)
def digit_match_bonus(local_code: str, system_code: str) -> float:
    """Bonus for exact natural account code match."""
    a = extract_natural_account(local_code or "")
    b = extract_natural_account(system_code or "")
    
    return 0.25 if (a and b and a == b) else 0.0
