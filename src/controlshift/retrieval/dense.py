"""Dense retrieval: SentenceTransformers embeddings in a FAISS inner-product index."""
from __future__ import annotations

from typing import Protocol

import numpy as np

from .corpus import Doc
from .hits import Hit

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 vectors, shape (len(texts), dim)."""


class SentenceTransformerEmbedder:
    """Lazy wrapper: the model is downloaded/loaded only on first use."""

    def __init__(self, name: str = DEFAULT_MODEL):
        self.name = name
        self._model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # heavy import, keep lazy

            self._model = SentenceTransformer(self.name)
        vecs = self._model.encode(texts, batch_size=32, convert_to_numpy=True,
                                  normalize_embeddings=True, show_progress_bar=False)
        return np.ascontiguousarray(vecs, dtype=np.float32)


class DenseIndex:
    def __init__(self, docs: list[Doc], index, embedder: Embedder):
        self.docs, self.index, self.embedder = docs, index, embedder

    @classmethod
    def build(cls, docs: list[Doc], embedder: Embedder) -> DenseIndex:
        import faiss

        vecs = embedder.encode([d.index_text for d in docs])
        index = faiss.IndexFlatIP(vecs.shape[1])  # exact cosine on normalised vectors
        index.add(vecs)
        return cls(docs, index, embedder)

    def search(self, query: str, k: int = 5, version: str | None = None) -> list[Hit]:
        import faiss

        if not query.strip():
            return []
        allowed = [i for i, d in enumerate(self.docs) if version is None or d.version == version]
        if not allowed:
            return []
        params = faiss.SearchParametersFlat() if hasattr(faiss, "SearchParametersFlat") else \
            faiss.SearchParameters()
        if version is not None:  # filter inside the search, before ranking
            params.sel = faiss.IDSelectorBatch(np.asarray(allowed, dtype=np.int64))
        qv = self.embedder.encode([query])
        scores, ids = self.index.search(qv, min(k, len(allowed)), params=params)
        return [Hit.from_doc(self.docs[i], r, s, "dense")
                for r, (s, i) in enumerate(zip(scores[0], ids[0], strict=True), start=1) if i >= 0]
