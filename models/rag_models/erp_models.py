from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class ScoredCandidate:
    """Scored COA candidate for a GL account"""
    system_id: str
    system_code: str
    system_name: str
    system_type: str
    system_category: str
    scores: Dict[str, float]
    aggregate: float


@dataclass
class Weights:
    """Scoring weights for ERP mapping"""
    type: float = 1.0
    semantic: float = 1.0
    fuzzy: float = 0.5
    category: float = 0.3
    code: float = 0.1
    numeric: float = 0.1
    digit_bonus: float = 0.1


@dataclass
class Thresholds:
    """Decision thresholds for ERP mapping"""
    auto: float = 0.80
    review: float = 0.75
