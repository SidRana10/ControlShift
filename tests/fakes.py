"""Offline stand-ins for the embedding and reranking models."""
import zlib

import numpy as np

from controlshift.retrieval.tokenize import tokenize


class FakeEmbedder:
    """Hashed bag-of-words vectors: deterministic, offline, lexically meaningful."""

    def __init__(self, name="fake-embedder-v1", dim=256, max_tokens=256):
        self.name, self.dim, self.max_tokens = name, dim, max_tokens

    def count_tokens(self, text):
        return len(text.split())

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in tokenize(t):
                out[i, zlib.crc32(tok.encode()) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-9)


class KeywordScorer:
    """Scores a passage by how many of the given keywords it contains."""

    name = "fake-reranker"

    def __init__(self, keywords):
        self.keywords = [k.lower() for k in keywords]
        self.calls = 0

    def score(self, query, passages):
        self.calls += 1
        return [float(sum(k in p.lower() for k in self.keywords)) for p in passages]
