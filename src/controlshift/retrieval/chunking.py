"""Length-aware embedding passages: split over-long texts into overlapping sentence windows.

Every sentence of the original body lands in at least one passage, so no source content is
dropped; passages are embedded, but results always point back to the parent chunk.
"""
from __future__ import annotations

import re

from .corpus import Doc
from .dense import Embedder

STRATEGY = "sentence-pack-v1"
DEFAULT_OVERLAP = 1
_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def make_passages(doc: Doc, embedder: Embedder, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """One passage if the text fits the embedder's limit, otherwise overlapping windows."""
    limit = embedder.max_tokens
    if embedder.count_tokens(doc.index_text) <= limit:
        return [doc.index_text]
    prefix = doc.index_prefix
    body = doc.index_text[len(prefix):]
    units: list[str] = []
    for sent in (s.strip() for s in _SPLIT.split(body)):
        if not sent:
            continue
        if embedder.count_tokens(prefix + sent) <= limit:
            units.append(sent)
            continue
        cur: list[str] = []  # a single over-long sentence: fall back to word windows
        for word in sent.split():
            if cur and embedder.count_tokens(prefix + " ".join([*cur, word])) > limit:
                units.append(" ".join(cur))
                cur = []
            cur.append(word)
        if cur:
            units.append(" ".join(cur))

    passages: list[str] = []
    cur_units: list[str] = []
    for unit in units:
        if cur_units and embedder.count_tokens(prefix + " ".join([*cur_units, unit])) > limit:
            passages.append(prefix + " ".join(cur_units))
            carry = cur_units[-overlap:] if overlap else []
            while carry and embedder.count_tokens(prefix + " ".join([*carry, unit])) > limit:
                carry = carry[1:]
            cur_units = carry
        cur_units.append(unit)
    if cur_units:
        passages.append(prefix + " ".join(cur_units))
    return passages
