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


class FakeProvider:
    """Scripted LLM: each call returns the next response (str | dict | Exception | callable)."""

    name = "fake"
    model = "fake-model-1"

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, system, prompt):
        import json

        self.calls.append((system, prompt))
        r = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if callable(r):
            r = r(system, prompt)
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r)


def answer(citations, text="Grounded answer.", **extra):
    base = {"answer": text, "citations": list(citations), "key_changes": [], "mappings": [],
            "uncertainties": [], "unresolved_questions": [], "abstained": False,
            "abstention_reason": None}
    return base | extra
