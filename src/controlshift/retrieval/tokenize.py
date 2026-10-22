"""Tokeniser shared by indexing and querying. Control IDs are kept as single normalised tokens."""
from __future__ import annotations

import re

from ..ingest.models import FUNCTION_NAMES, normalize_control_id

TOKENIZER_VERSION = "1"
STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from", "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "these", "this", "to", "was", "were", "which", "with", "within", "without", "not", "can", "may", "should", "would", "will"])

_ID_RE = re.compile(r"\b([A-Za-z]{2})\.([A-Za-z]{2})(?:-(\d{1,2}))?\b")
_WORD_RE = re.compile(r"[a-z0-9]+")


def _stem(word: str) -> str:
    """Minimal plural folding (policies/policy handled by shared 'ies' -> 'y')."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    """Words (lowercased, stop-words dropped, plurals folded) plus control-ID tokens.

    'PR.AT-1' and 'pr.at-01' both yield 'pr.at-01' and its category token 'pr.at'.
    """
    tokens: list[str] = []

    def take_id(m: re.Match) -> str:
        fn, cat, num = m.group(1).upper(), m.group(2).upper(), m.group(3)
        if fn not in FUNCTION_NAMES:
            return m.group(0)
        tokens.append(f"{fn}.{cat}".lower())
        if num:
            tokens.append(normalize_control_id(f"{fn}.{cat}-{num}").lower())
        return " "

    rest = _ID_RE.sub(take_id, text)
    tokens += [_stem(w) for w in _WORD_RE.findall(rest.lower()) if w not in STOPWORDS]
    return tokens


def preprocessing_settings() -> dict:
    """Everything about text preprocessing that must invalidate a cached index when changed."""
    return {"tokenizer_version": TOKENIZER_VERSION, "stopwords": sorted(STOPWORDS),
            "index_text": "control-title-context-v1"}
