"""Business rules for ERP account mapping."""

from functools import lru_cache
from .normalization import token_set

# Mutually exclusive account patterns
MUTEX_SETS = [
    (frozenset({"tax", "taxes", "income", "federal"}), 
     frozenset({"meal", "meals", "entertainment", "travel", "food", "dining"})),
    (frozenset({"payroll", "wages", "salary", "salaries"}), 
     frozenset({"meal", "meals", "entertainment", "travel"})),
    (frozenset({"interest"}), 
     frozenset({"meal", "meals", "entertainment", "travel", "tax", "taxes"})),
]


@lru_cache(maxsize=4096)
def mutex_penalty(local_name: str, sys_name: str) -> float:
    """Calculate penalty for mutually exclusive account patterns."""
    lt = token_set(local_name)
    st = token_set(sys_name)
    
    penalty = 0.0
    for a, b in MUTEX_SETS:
        if (lt & a and st & b) or (lt & b and st & a):
            penalty += 0.25
    
    return min(penalty, 0.6)


@lru_cache(maxsize=4096)
def keyword_boost(local_name: str, sys_name: str) -> float:
    """Boost score for specific keyword matches."""
    lt = token_set(local_name)
    st = token_set(sys_name)
    
    meals_ent = frozenset({"meals", "entertainment"})
    return 0.15 if (meals_ent & lt) and (meals_ent & st) else 0.0


@lru_cache(maxsize=4096)
def subset_boost(local_name: str, sys_name: str) -> float:
    """Boost score if local name is subset of system name."""
    lt = token_set(local_name)
    st = token_set(sys_name)
    
    return 0.12 if (lt and lt.issubset(st)) else 0.0
