"""Process-wide services, built once at application start and reused by every request."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

from ..evidence.assemble import EvidenceAssembler
from ..evidence.bundle import EvidenceBundle
from ..generation.config import Settings
from ..generation.generate import GenerationResult, GroundedGenerator
from ..generation.provider import LLMProvider, provider_from_settings
from ..store.queries import KnowledgeStore


@dataclass
class Services:
    db_path: Path
    settings: Settings
    retriever: object | None  # callable (query, k, version) -> hits, or None
    retrieval_label: str
    provider: LLMProvider | None
    models_loaded: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def answer(self, question: str, k: int, generate: bool) -> tuple[EvidenceBundle, GenerationResult]:
        # SQLite connections are per-request (cheap, read-only); models are shared, so retrieval
        # (not DB reads) is serialised.
        with KnowledgeStore(self.db_path) as store:
            guarded = None
            if self.retriever is not None:
                def guarded(q, kk, v):
                    with self._lock:
                        return self.retriever(q, kk, v)
            bundle = EvidenceAssembler(store, guarded, self.retrieval_label, k=k).assemble(question)
            gen = GroundedGenerator(self.provider if generate else None, self.settings)
            return bundle, gen.generate(bundle, store)

    def health(self) -> dict:
        with KnowledgeStore(self.db_path) as store:
            c = store.conn
            db = {"chunks": c.execute("SELECT COUNT(*) FROM chunk").fetchone()[0],
                  "elements": c.execute("SELECT COUNT(*) FROM element").fetchone()[0],
                  "crosswalk_rows": c.execute("SELECT COUNT(*) FROM crosswalk_mapping").fetchone()[0]}
        return {"status": "ok", "database": db,
                "retrieval": {"mode": self.retrieval_label, "models_loaded": self.models_loaded},
                "llm": {"configured": self.provider is not None,
                        "provider": self.provider.name if self.provider else None,
                        "model": self.provider.model if self.provider else None}}


def build_services(settings: Settings | None = None) -> Services:
    """Load the database, indexes and models once. Dense search uses the NumPy backend on macOS."""
    from ..evidence.cli import build_retriever

    s = settings or Settings.from_env()
    retriever, label = build_retriever(s.retrieval_mode, s.db_path, s.index_dir)
    loaded = {"none": [], "bm25": [], "dense": ["embedder"], "hybrid": ["embedder"],
              "hybrid_rerank": ["embedder", "cross-encoder"]}[s.retrieval_mode]
    if "embedder" in loaded:  # force the lazy model load now, not on the first request
        retriever("warm-up", 1, None)
    return Services(s.db_path, s, retriever, label, provider_from_settings(s), loaded)
