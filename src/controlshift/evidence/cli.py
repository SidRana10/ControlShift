"""`controlshift-evidence "<question>"`: print the assembled evidence bundle as JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..retrieval.corpus import CorpusError, load_corpus
from ..retrieval.dense import (
    DEFAULT_MODEL,
    SentenceTransformerEmbedder,
    UnsafeBackendError,
    resolve_backend,
)
from ..retrieval.hybrid import HybridConfig, HybridRetriever
from ..retrieval.persist import DEFAULT_INDEX_DIR, IndexStaleError, load_bm25, load_dense
from ..retrieval.reranker import CrossEncoderScorer
from ..store.queries import KnowledgeStore
from .assemble import EvidenceAssembler, validate_bundle

MODES = ["none", "bm25", "dense", "hybrid", "hybrid_rerank"]


def build_retriever(mode: str, db: Path, index_dir: Path):
    """(callable (query, k, version) -> hits, label) for a retrieval mode, or (None, 'none')."""
    if mode == "none":
        return None, "none"
    docs = load_corpus(db)
    if mode == "bm25":
        return load_bm25(index_dir, docs).search, mode
    resolve_backend()  # refuse unsafe configurations before loading a model
    dense = load_dense(index_dir, SentenceTransformerEmbedder(DEFAULT_MODEL), docs)
    if mode == "dense":
        return dense.search, mode
    retriever = HybridRetriever(load_bm25(index_dir, docs), dense,
                                CrossEncoderScorer() if mode == "hybrid_rerank" else None,
                                HybridConfig())
    rerank = mode == "hybrid_rerank"
    return (lambda q, k, v: retriever.search(q, k, v, rerank_results=rerank)), mode


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="controlshift-evidence", description=__doc__)
    ap.add_argument("question")
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    ap.add_argument("--retrieval", choices=MODES, default="hybrid",
                    help="passage retrieval mode ('none' = structured records only)")
    ap.add_argument("-k", type=int, default=5, help="passages per version")
    ap.add_argument("--compact", action="store_true", help="single-line JSON")
    args = ap.parse_args(argv)
    try:
        retriever, label = build_retriever(args.retrieval, args.db, args.index_dir)
        with KnowledgeStore(args.db) as store:
            bundle = EvidenceAssembler(store, retriever, label, k=args.k).assemble(args.question)
            out = bundle.to_dict()
            out["citation_validation"] = validate_bundle(store, bundle)
    except (CorpusError, IndexStaleError, UnsafeBackendError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
