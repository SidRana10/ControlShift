"""Reciprocal Rank Fusion over ranked hit lists (ranks only; raw scores are ignored)."""
from __future__ import annotations

import dataclasses

from .hits import Hit

DEFAULT_RRF_K = 60


def rrf_fuse(rankings: dict[str, list[Hit]], k: int = DEFAULT_RRF_K) -> list[Hit]:
    """Fuse named ranked lists: score(d) = sum over lists of 1 / (k + rank_in_list).

    Duplicates (same chunk_id) are merged, keeping the first-seen metadata. Ties are broken by
    best (lowest) rank in any list, then by chunk_id, so output is fully deterministic.
    """
    if k < 0:
        raise ValueError("rrf k must be >= 0")
    merged: dict[str, dict] = {}
    for name in sorted(rankings):  # fixed iteration order, independent of dict insertion order
        seen: set[str] = set()
        for position, hit in enumerate(rankings[name], start=1):
            if hit.chunk_id in seen:  # a malformed list repeating an ID counts only once
                continue
            seen.add(hit.chunk_id)
            entry = merged.setdefault(hit.chunk_id, {"hit": hit, "score": 0.0, "components": {}})
            entry["score"] += 1.0 / (k + position)
            entry["components"][name] = {"rank": position, "score": hit.score}
    ordered = sorted(
        merged.items(),
        key=lambda kv: (-kv[1]["score"], min(c["rank"] for c in kv[1]["components"].values()),
                        kv[0]))
    out = []
    for rank, (_, e) in enumerate(ordered, start=1):
        base: Hit = e["hit"]
        comps = {**e["components"], "rrf": {"rank": rank, "score": e["score"]}}
        out.append(dataclasses.replace(base, rank=rank, score=e["score"], mode="hybrid",
                                       components=comps))
    return out
