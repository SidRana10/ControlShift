"""`controlshift-retrieve`: build indexes and run BM25 / dense searches."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .corpus import CorpusError, load_corpus
from .dense import (
    BACKENDS,
    DEFAULT_MODEL,
    SentenceTransformerEmbedder,
    UnsafeBackendError,
    resolve_backend,
)
from .fusion import DEFAULT_RRF_K
from .hybrid import HybridConfig, HybridRetriever
from .persist import (
    DEFAULT_INDEX_DIR,
    IndexStaleError,
    build_bm25,
    build_dense,
    dir_size_bytes,
    load_bm25,
    load_dense,
)
from .reranker import DEFAULT_RERANKER, CrossEncoderScorer


def _print_hits(hits, as_json: bool, debug: bool = False) -> None:
    if as_json:
        print(json.dumps([h.to_dict() for h in hits], indent=2, ensure_ascii=False))
        return
    if not hits:
        print("(no results)")
    for h in hits:
        snippet = h.text.replace("\n", " ")
        snippet = snippet[:160] + ("..." if len(snippet) > 160 else "")
        print(f"{h.rank}. [{h.score:.4f}] {h.chunk_id}  v{h.version}  "
              f"{h.control_id or '-'}  {h.source_file} p.{h.page}")
        print(f"   {h.section}\n   {snippet}")
        if debug and h.components:
            print("   stages: " + ", ".join(f"{n}=#{c['rank']} ({c['score']:.4f})"
                                            for n, c in h.components.items()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="controlshift-retrieve", description=__doc__)
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    ap.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformers model id")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-index", help="build (or reuse a fresh) index")
    b.add_argument("--mode", choices=["bm25", "dense", "all"], default="all")
    b.add_argument("--force", action="store_true", help="rebuild even if the cache is fresh")
    s = sub.add_parser("search", help="search an index")
    s.add_argument("query")
    s.add_argument("--mode", choices=["bm25", "dense", "hybrid", "hybrid_rerank"], required=True)
    s.add_argument("--version", choices=["1.1", "2.0"], help="restrict candidates to one version")
    s.add_argument("-k", type=int, default=5)
    s.add_argument("--json", action="store_true")
    s.add_argument("--debug", action="store_true", help="show per-stage ranks and scores")
    s.add_argument("--dense-backend", choices=BACKENDS, default="auto",
                   help="exact search backend (auto = numpy on macOS; see retrieval/dense.py)")
    s.add_argument("--rrf-k", type=int, default=DEFAULT_RRF_K)
    s.add_argument("--pool", type=int, default=30, help="candidates per retriever for fusion")
    s.add_argument("--rerank-pool", type=int, default=30, help="fused candidates to rerank")
    s.add_argument("--reranker-model", default=DEFAULT_RERANKER)
    args = ap.parse_args(argv)

    try:
        if args.cmd == "search" and args.mode != "bm25":
            resolve_backend(args.dense_backend)  # fail fast, before loading any model
        docs = load_corpus(args.db)
        if args.cmd == "build-index":
            if args.mode in ("bm25", "all"):
                status, m = build_bm25(docs, args.index_dir, args.force)
                print(f"bm25: {status} ({m['n_docs']} docs)")
            if args.mode in ("dense", "all"):
                status, m = build_dense(docs, args.index_dir, SentenceTransformerEmbedder(args.model),
                                        args.force)
                print(f"dense: {status} ({m['n_docs']} docs, dim {m['dim']}, model {m['model']})")
            print(f"index size: {dir_size_bytes(args.index_dir)} bytes in {args.index_dir}")
            return 0
        if args.mode == "bm25":
            hits = load_bm25(args.index_dir, docs).search(args.query, args.k, args.version)
        elif args.mode == "dense":
            hits = load_dense(args.index_dir, SentenceTransformerEmbedder(args.model), docs,
                       backend=args.dense_backend).search(args.query, args.k, args.version)
        else:
            retriever = HybridRetriever(
                load_bm25(args.index_dir, docs),
                load_dense(args.index_dir, SentenceTransformerEmbedder(args.model), docs,
                           backend=args.dense_backend),
                CrossEncoderScorer(args.reranker_model) if args.mode == "hybrid_rerank" else None,
                HybridConfig(args.rrf_k, args.pool, args.rerank_pool))
            hits = retriever.search(args.query, args.k, args.version,
                                    rerank_results=args.mode == "hybrid_rerank")
        _print_hits(hits, args.json, args.debug)
        return 0
    except (CorpusError, IndexStaleError, UnsafeBackendError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
