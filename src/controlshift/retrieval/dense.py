"""Dense retrieval: SentenceTransformers embeddings in a FAISS inner-product index.

Docs longer than the model's input limit are embedded as several passages; a document's
score is the best score among its passages.

Search backends (identical results; the index is a flat, exact inner-product index):
  * "faiss"  - FAISS search (refused on macOS unless CONTROLSHIFT_ALLOW_UNSAFE_FAISS=1).
  * "numpy"  - one matrix product over the vectors stored in the FAISS index.
  * "auto"   - numpy on macOS, faiss elsewhere (override with CONTROLSHIFT_DENSE_BACKEND).

Why: the macOS wheels of faiss-cpu and torch each bundle their *own* libomp.dylib
(faiss/.dylibs/libomp.dylib, torch/lib/libomp.dylib). LLVM's OpenMP runtime aborts the process
("OMP: Error #15") as soon as a second copy is *used*, i.e. once both a FAISS search and a torch
parallel op have run in one process, in either order. Import order, thread limits and
OMP_NUM_THREADS do not help. FAISS is still used to build, persist and load the index (adding
vectors and reading them back do not start its OpenMP runtime); only the search step avoids it.
"""
from __future__ import annotations

import os
import sys
from typing import Protocol

import numpy as np

from .corpus import Doc
from .hits import Hit

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MAX_TOKENS = 256  # all-MiniLM-L6-v2's input limit
BACKENDS = ("auto", "faiss", "numpy")
ALLOW_UNSAFE_ENV = "CONTROLSHIFT_ALLOW_UNSAFE_FAISS"


class UnsafeBackendError(ValueError):
    """The requested dense search backend would risk aborting the process on this platform."""


def resolve_backend(backend: str | None = None) -> str:
    """Resolve 'auto'/None (and the CONTROLSHIFT_DENSE_BACKEND override) to 'faiss' or 'numpy'."""
    choice = backend or os.environ.get("CONTROLSHIFT_DENSE_BACKEND") or "auto"
    if choice not in BACKENDS:
        raise ValueError(f"unknown dense backend {choice!r}; choose from {BACKENDS}")
    if choice == "auto":
        return "numpy" if sys.platform == "darwin" else "faiss"
    if choice == "faiss" and sys.platform == "darwin" and os.environ.get(ALLOW_UNSAFE_ENV) != "1":
        raise UnsafeBackendError(
            "The 'faiss' search backend is disabled on macOS: faiss-cpu and torch bundle separate "
            "OpenMP runtimes, and using both in one process aborts the interpreter "
            "(OMP: Error #15). Use '--dense-backend numpy' (or 'auto'), which gives identical "
            f"results. For diagnostics only, set {ALLOW_UNSAFE_ENV}=1 to override.")
    return choice


class Embedder(Protocol):
    name: str
    max_tokens: int

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 vectors, shape (len(texts), dim)."""

    def count_tokens(self, text: str) -> int:
        """Number of model tokens (including special tokens) for `text`."""


class SentenceTransformerEmbedder:
    """Lazy wrapper: the model is downloaded/loaded only on first use."""

    def __init__(self, name: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.name, self.max_tokens = name, max_tokens
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # heavy import, keep lazy

            self._model = SentenceTransformer(self.name)
            self._model.max_seq_length = min(self._model.max_seq_length or self.max_tokens,
                                             self.max_tokens)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self._load().encode(texts, batch_size=32, convert_to_numpy=True,
                                   normalize_embeddings=True, show_progress_bar=False)
        return np.ascontiguousarray(vecs, dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        return len(self._load().tokenizer(text, add_special_tokens=True)["input_ids"])


class DenseIndex:
    def __init__(self, docs: list[Doc], index, embedder: Embedder, passage_doc: list[int],
                 passage_text: list[str], backend: str | None = None):
        if index.ntotal != len(passage_doc) or len(passage_doc) != len(passage_text):
            raise ValueError("passage bookkeeping does not match the FAISS index")
        self.docs, self.index, self.embedder = docs, index, embedder
        self.passage_doc, self.passage_text = passage_doc, passage_text
        self.backend = resolve_backend(backend)
        self._matrix: np.ndarray | None = None

    @classmethod
    def build(cls, docs: list[Doc], embedder: Embedder, overlap: int = 1,
              backend: str | None = None) -> DenseIndex:
        import faiss

        from .chunking import make_passages

        passage_doc: list[int] = []
        passage_text: list[str] = []
        for i, d in enumerate(docs):
            for p in make_passages(d, embedder, overlap):
                passage_doc.append(i)
                passage_text.append(p)
        vecs = embedder.encode(passage_text)
        index = faiss.IndexFlatIP(vecs.shape[1])  # exact cosine on normalised vectors
        index.add(vecs)
        return cls(docs, index, embedder, passage_doc, passage_text, backend)

    def _vectors(self) -> np.ndarray:
        if self._matrix is None:  # exact copy of the stored vectors (flat index)
            self._matrix = self.index.reconstruct_n(0, self.index.ntotal)
        return self._matrix

    def _top_passages(self, qv: np.ndarray, allowed: list[int], n: int):
        """Best `n` passages among `allowed`, as (scores, passage ids), best first."""
        if self.backend == "numpy":
            ids = np.asarray(allowed, dtype=np.int64)
            scores = self._vectors()[ids] @ qv[0]
            order = np.lexsort((ids, -scores))[:n]  # score desc, then passage id
            return scores[order], ids[order]
        import faiss

        params = faiss.SearchParametersFlat() if hasattr(faiss, "SearchParametersFlat") else \
            faiss.SearchParameters()
        params.sel = faiss.IDSelectorBatch(np.asarray(allowed, dtype=np.int64))  # pre-filter
        scores, ids = self.index.search(qv, n, params=params)
        return scores[0], ids[0]

    def search(self, query: str, k: int = 5, version: str | None = None) -> list[Hit]:
        if not query.strip() or k <= 0:
            return []
        allowed = [p for p, i in enumerate(self.passage_doc)
                   if version is None or self.docs[i].version == version]
        if not allowed:
            return []
        qv = self.embedder.encode([query])
        n = min(len(allowed), max(k, 1) * 4)
        while True:
            scores, ids = self._top_passages(qv, allowed, n)  # filter applied before ranking
            best: dict[int, tuple[float, int]] = {}
            for s, p in zip(scores, ids, strict=True):
                if p < 0:
                    continue
                doc = self.passage_doc[p]
                if doc not in best:  # results come sorted, so the first passage is the doc's best
                    best[doc] = (float(s), int(p))
            # With >= k distinct docs among the n best passages, the top-k docs are exact.
            if len(best) >= k or n >= len(allowed):
                break
            n = min(len(allowed), n * 2)
        ranked = sorted(best.items(), key=lambda kv: (-kv[1][0], kv[0]))[:k]
        out = []
        for r, (doc_i, (s, p)) in enumerate(ranked, start=1):
            hit = Hit.from_doc(self.docs[doc_i], r, s, "dense")
            if self.passage_text[p] != self.docs[doc_i].index_text:
                hit.matched_passage = self.passage_text[p]
            out.append(hit)
        return out
