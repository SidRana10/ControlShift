"""BM25 (rank-bm25) with version filtering applied *before* scoring."""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from .corpus import Doc
from .hits import Hit
from .tokenize import tokenize


class BM25Index:
    """One BM25Okapi per framework version (+ one over everything), so IDF statistics are
    computed only over the documents a filtered query is allowed to return."""

    def __init__(self, docs: list[Doc], tokens: list[list[str]]):
        if len(docs) != len(tokens):
            raise ValueError("docs/tokens length mismatch")
        self.docs = docs
        self.tokens = tokens
        self._groups: dict[str | None, tuple[list[int], BM25Okapi]] = {}

    @classmethod
    def build(cls, docs: list[Doc]) -> BM25Index:
        return cls(docs, [tokenize(d.index_text) for d in docs])

    def _group(self, version: str | None) -> tuple[list[int], BM25Okapi] | None:
        if version not in self._groups:
            idx = [i for i, d in enumerate(self.docs) if version is None or d.version == version]
            self._groups[version] = (idx, BM25Okapi([self.tokens[i] for i in idx])) if idx else (
                [], None)  # type: ignore[assignment]
        idx, bm25 = self._groups[version]
        return (idx, bm25) if idx else None

    def search(self, query: str, k: int = 5, version: str | None = None) -> list[Hit]:
        q = tokenize(query)
        group = self._group(version) if q else None
        if group is None:
            return []
        idx, bm25 = group
        scores = bm25.get_scores(q)
        # stable order: score desc, then corpus order
        ranked = sorted(range(len(idx)), key=lambda j: (-scores[j], j))
        out: list[Hit] = []
        for j in ranked:
            if scores[j] <= 0 or len(out) >= k:
                break
            out.append(Hit.from_doc(self.docs[idx[j]], len(out) + 1, scores[j], "bm25"))
        return out
