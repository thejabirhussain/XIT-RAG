"""Fuzzy string matching service with fallback."""

try:
    from rapidfuzz import fuzz

    def fuzzy_similarity(a: str, b: str) -> float:
        """Returns similarity score between 0.0 and 1.0"""
        return fuzz.token_set_ratio(a, b) / 100.0

except ImportError:
    from difflib import SequenceMatcher

    def fuzzy_similarity(a: str, b: str) -> float:
        """Fallback fuzzy similarity using difflib"""
        return SequenceMatcher(None, a, b).ratio()
