"""Hybrid retrieval pipeline: BM25 + dense -> RRF -> optional cross-encoder rerank."""
from __future__ import annotations

from dataclasses import dataclass

from .bm25 import BM25Index
from .dense import DenseIndex
from .fusion import DEFAULT_RRF_K, rrf_fuse
from .hits import Hit
from .reranker import Scorer, rerank


@dataclass(frozen=True)
class HybridConfig:
    rrf_k: int = DEFAULT_RRF_K
    pool: int = 30  # candidates taken from each retriever
    rerank_pool: int = 30  # fused candidates passed to the cross-encoder


class HybridRetriever:
    def __init__(self, bm25: BM25Index, dense: DenseIndex, scorer: Scorer | None = None,
                 config: HybridConfig = HybridConfig()):  # noqa: B008 (frozen dataclass)
        self.bm25, self.dense, self.scorer, self.config = bm25, dense, scorer, config
        self._passages = {d.chunk_id: d.index_text for d in dense.docs}

    def fuse(self, query: str, version: str | None = None) -> list[Hit]:
        """Full fused ranking (version filter applied inside both retrievers)."""
        c = self.config
        return rrf_fuse({"bm25": self.bm25.search(query, c.pool, version),
                         "dense": self.dense.search(query, c.pool, version)}, c.rrf_k)

    def search(self, query: str, k: int = 5, version: str | None = None,
               rerank_results: bool = False) -> list[Hit]:
        fused = self.fuse(query, version)
        if not rerank_results:
            return fused[:k]
        if self.scorer is None:
            raise ValueError("a reranker is required for hybrid_rerank")
        pool = fused[: self.config.rerank_pool]
        return rerank(query, pool, self._passages, self.scorer, k)
