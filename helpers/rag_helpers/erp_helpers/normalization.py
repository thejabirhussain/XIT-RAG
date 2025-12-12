"""Text normalization for ERP account mapping."""

import re
from functools import lru_cache
from typing import Optional

DEFAULT_SYNONYMS = {
    "ap": "accounts payable", "a p": "accounts payable", "a/p": "accounts payable",
    "ar": "accounts receivable", "a r": "accounts receivable", "a/r": "accounts receivable",
    "payables": "accounts payable", "receivables": "accounts receivable",
    "unearned revenue": "deferred revenue", "sales tax": "indirect tax",
    "ppe": "property plant and equipment", "fixed assets": "property plant and equipment",
    "cogs": "cost of goods sold", "cost of sales": "cost of goods sold",
    "lt": "long term", "LT": "long term", "l/t": "long term",
    "depr": "depreciation", "income tax": "tax", "income taxes": "taxes",
}

STOPWORDS = frozenset({
    "the", "and", "of", "for", "to", "on", "in", "-", "&", "at", "by", "with",
    "expense", "expenses", "items", "item", "account", "accounts"
})

_re_punct = re.compile(r"[^\w\s\-]")
_re_ws = re.compile(r"\s+")
_nat_re = re.compile(r"(\d{3,6})(?!.*\d)")


@lru_cache(maxsize=8192)
def normalize_text(s: str) -> str:
    """Normalize text with synonym replacement and stopword removal."""
    s = (s or "").lower().strip()
    s = s.replace("&", " and ")
    s = s.replace("a/p", "accounts payable").replace("a\\p", "accounts payable")
    s = s.replace("a/r", "accounts receivable").replace("a\\r", "accounts receivable")
    s = _re_punct.sub(" ", s)
    s = _re_ws.sub(" ", s).strip()
    
    for k, v in DEFAULT_SYNONYMS.items():
        s = re.sub(rf"\b{re.escape(k)}\b", v, s)
    
    return " ".join(t for t in s.split() if t not in STOPWORDS)


@lru_cache(maxsize=4096)
def token_set(s: str) -> frozenset:
    """Get token set from normalized text."""
    return frozenset(normalize_text(s).replace("-", " ").split()) if s else frozenset()


@lru_cache(maxsize=1024)
def normalize_type(s: str) -> str:
    """Normalize account type."""
    t = (s or "").strip().lower()
    if not t:
        return ""
    if "expense" in t or "deduction" in t or "opex" in t:
        return "expense"
    if "revenue" in t or "income" in t or "sales" in t:
        return "revenue"
    if "liabil" in t:
        return "liability"
    if "asset" in t:
        return "asset"
    if "equity" in t or "capital" in t or "net asset" in t:
        return "equity"
    if "cogs" in t or "cost of goods" in t or "cost of sales" in t:
        return "cogs"
    return t


@lru_cache(maxsize=2048)
def extract_natural_account(code: Optional[str]) -> Optional[str]:
    """Extract natural account number from GL code."""
    if not code:
        return None
    
    # Try segmented format (e.g., 1-2-3456)
    parts = str(code).replace("-", ".").split(".")
    if len(parts) >= 3 and parts[2].isdigit():
        stripped = parts[2].lstrip("0")
        return stripped or parts[2]
    
    # Try regex pattern
    m = _nat_re.search((code or "").replace(" ", ""))
    if not m:
        return None
    
    nat = m.group(1).lstrip("0")
    return nat or m.group(1)
