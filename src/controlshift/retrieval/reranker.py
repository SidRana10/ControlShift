"""Cross-encoder reranking (cross-encoder/ms-marco-MiniLM-L-6-v2), cached per process."""
from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable
from typing import Protocol

from .hits import Hit

DEFAULT_RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_MODELS: dict[str, object] = {}  # process-level cache: model name -> loaded CrossEncoder


class Scorer(Protocol):
    name: str

    def score(self, query: str, passages: list[str]) -> list[float]: ...


def split_to_fit(passage: str, budget: int, count: Callable[[str], int]) -> list[str]:
    """Return [passage] if it fits `budget` tokens, else sentence windows that each fit.

    Used so long passages are scored in full (max over windows) rather than truncated.
    """
    if count(passage) <= budget:
        return [passage]
    windows: list[str] = []
    cur: list[str] = []
    for unit in (u for u in re.split(r"(?<=[.!?])\s+|\n+", passage) if u.strip()):
        if count(unit) > budget:  # a single over-long sentence: fall back to word windows
            words = unit.split()
            unit_parts, part = [], []
            for w in words:
                if part and count(" ".join([*part, w])) > budget:
                    unit_parts.append(" ".join(part))
                    part = []
                part.append(w)
            unit_parts.append(" ".join(part))
        else:
            unit_parts = [unit]
        for u in unit_parts:
            if cur and count(" ".join([*cur, u])) > budget:
                windows.append(" ".join(cur))
                cur = []
            cur.append(u)
    if cur:
        windows.append(" ".join(cur))
    return windows


class CrossEncoderScorer:
    def __init__(self, name: str = DEFAULT_RERANKER, max_length: int = 512):
        self.name, self.max_length = name, max_length
        self.windowed = 0  # passages that did not fit max_length and were scored in windows

    def _model(self):
        if self.name not in _MODELS:
            from sentence_transformers import CrossEncoder  # heavy import, keep lazy

            _MODELS[self.name] = CrossEncoder(self.name, max_length=self.max_length)
        return _MODELS[self.name]

    def score(self, query: str, passages: list[str]) -> list[float]:
        """Relevance of each passage to the query; over-long (query, passage) pairs are never
        truncated - the passage is split into windows and the best window score is used."""
        if not passages:
            return []
        model = self._model()
        tok = model.tokenizer

        def count(text: str) -> int:
            return len(tok(text, add_special_tokens=False)["input_ids"])

        budget = self.max_length - count(query) - 3  # [CLS] query [SEP] passage [SEP]
        if budget < 16:
            raise ValueError("query too long for the reranker input window")
        pairs: list[tuple[str, str]] = []
        owner: list[int] = []
        for i, passage in enumerate(passages):
            parts = split_to_fit(passage, budget, count)
            self.windowed += len(parts) > 1
            pairs += [(query, part) for part in parts]
            owner += [i] * len(parts)
        raw = model.predict(pairs, batch_size=16, show_progress_bar=False)
        best = [float("-inf")] * len(passages)
        for i, s in zip(owner, raw, strict=True):
            best[i] = max(best[i], float(s))
        return best


def rerank(query: str, hits: list[Hit], passages: dict[str, str], scorer: Scorer,
           top_k: int | None = None) -> list[Hit]:
    """Re-order `hits` by cross-encoder relevance. Prior ranks/scores move into `components`.

    `passages` maps chunk_id -> text shown to the model. Ties fall back to the incoming
    rank, then chunk_id.
    """
    if not hits or not query.strip():
        return []
    scores = scorer.score(query, [passages[h.chunk_id] for h in hits])
    ordered = sorted(zip(hits, scores, strict=True), key=lambda t: (-t[1], t[0].rank, t[0].chunk_id))
    out = []
    for rank, (hit, s) in enumerate(ordered[:top_k], start=1):
        comps = {**hit.components, hit.mode: {"rank": hit.rank, "score": hit.score},
                 "rerank": {"rank": rank, "score": s}}
        out.append(dataclasses.replace(hit, rank=rank, score=s, mode="hybrid_rerank",
                                       components=comps))
    return out
