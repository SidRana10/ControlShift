"""`controlshift-retrieve`: build indexes and run BM25 / dense searches."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .corpus import CorpusError, load_corpus
from .dense import DEFAULT_MODEL, SentenceTransformerEmbedder
from .persist import (
    DEFAULT_INDEX_DIR,
    IndexStaleError,
    build_bm25,
    build_dense,
    dir_size_bytes,
    load_bm25,
    load_dense,
)


def _print_hits(hits, as_json: bool) -> None:
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
    s.add_argument("--mode", choices=["bm25", "dense"], required=True)
    s.add_argument("--version", choices=["1.1", "2.0"], help="restrict candidates to one version")
    s.add_argument("-k", type=int, default=5)
    s.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
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
            index = load_bm25(args.index_dir, docs)
        else:
            index = load_dense(args.index_dir, SentenceTransformerEmbedder(args.model), docs)
        _print_hits(index.search(args.query, args.k, args.version), args.json)
        return 0
    except (CorpusError, IndexStaleError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
