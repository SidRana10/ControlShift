"""Runs the retrieval benchmark and writes eval/results.json and eval/report.md.

    python eval/benchmark.py [--reps 5] [--questions eval/questions.jsonl]

Models are loaded once. Cold start (process-cold, OS file cache warm) is timed separately from warm
per-query latency. Quality metrics are deterministic; latencies are not.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import sys
import time
from pathlib import Path

from controlshift.evaluation.dataset import DatasetError, load_questions, validate
from controlshift.evaluation.report import render_report
from controlshift.evaluation.runner import (
    MODES,
    TOP_K,
    evaluate,
    git_commit,
    hardware,
    library_versions,
    measure_latency,
    measure_stages,
)
from controlshift.retrieval.corpus import load_corpus
from controlshift.retrieval.dense import DEFAULT_MODEL, SentenceTransformerEmbedder, resolve_backend
from controlshift.retrieval.fusion import rrf_fuse
from controlshift.retrieval.hybrid import HybridConfig, HybridRetriever
from controlshift.retrieval.persist import load_bm25, load_dense
from controlshift.retrieval.reranker import DEFAULT_RERANKER, CrossEncoderScorer, rerank


def dataset_summary(queries, path: Path) -> dict:
    rel = [r for q in queries for r in q.relevant]
    return {
        "n_total": len(queries), "n_final": sum(q.status == "final" for q in queries),
        "n_provisional": sum(q.status == "provisional" for q in queries),
        "by_category": dict(collections.Counter(q.category for q in queries)),
        "by_difficulty": dict(collections.Counter(q.difficulty for q in queries)),
        "n_filtered": sum(q.version_filter is not None for q in queries),
        "mean_relevant": len(rel) / len(queries),
        "n_grade2": sum(r.grade == 2 for r in rel), "n_grade1": sum(r.grade == 1 for r in rel),
        "human_reviewed": any(q.human_reviewed for q in queries),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--index-dir", type=Path, default=Path("data/indexes"))
    ap.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=Path("eval"))
    ap.add_argument("--reps", type=int, default=5, help="timed passes over all questions")
    ap.add_argument("--render-only", action="store_true",
                    help="regenerate report.md from the existing results.json (no measurements)")
    args = ap.parse_args()
    if args.render_only:
        data = json.loads((args.out_dir / "results.json").read_text(encoding="utf-8"))
        (args.out_dir / "report.md").write_text(render_report(data), encoding="utf-8")
        print(f"rewrote {args.out_dir}/report.md from results.json")
        return 0

    try:
        queries = load_questions(args.questions)
    except DatasetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors := validate(queries, args.db):
        print("dataset invalid:\n" + "\n".join(errors), file=sys.stderr)
        return 2

    cold = {}
    t = time.perf_counter()
    docs = load_corpus(args.db)
    cold["load_corpus_from_sqlite"] = time.perf_counter() - t
    t = time.perf_counter()
    bm25 = load_bm25(args.index_dir, docs)
    cold["load_bm25_index"] = time.perf_counter() - t
    embedder = SentenceTransformerEmbedder(DEFAULT_MODEL)
    t = time.perf_counter()
    dense = load_dense(args.index_dir, embedder, docs)
    cold["load_faiss_index"] = time.perf_counter() - t
    t = time.perf_counter()
    embedder.encode(["warm up"])  # imports torch + loads the sentence-transformer
    cold["load_embedding_model_and_first_encode"] = time.perf_counter() - t
    scorer = CrossEncoderScorer(DEFAULT_RERANKER)
    t = time.perf_counter()
    scorer.score("warm up", ["warm up passage"])  # loads the cross-encoder
    cold["load_cross_encoder_and_first_score"] = time.perf_counter() - t

    config = HybridConfig()
    retriever = HybridRetriever(bm25, dense, scorer, config)
    searches = {
        "bm25": bm25.search,
        "dense": dense.search,
        "hybrid": lambda q, k, v: retriever.search(q, k, v, rerank_results=False),
        "hybrid_rerank": lambda q, k, v: retriever.search(q, k, v, rerank_results=True),
    }
    assert list(searches) == MODES

    print("evaluating quality ...", flush=True)
    quality = evaluate(queries, searches, TOP_K)

    print(f"measuring latency ({args.reps} timed passes) ...", flush=True)
    latency_modes = measure_latency(queries, searches, reps=args.reps, k=TOP_K)
    # Stage breakdown of the hybrid pipeline (inputs are precomputed so each stage is isolated).
    bm_lists = {q.query_id: bm25.search(q.question, config.pool, q.version_filter) for q in queries}
    dn_lists = {q.query_id: dense.search(q.question, config.pool, q.version_filter) for q in queries}
    fused = {q.query_id: rrf_fuse({"bm25": bm_lists[q.query_id], "dense": dn_lists[q.query_id]},
                                  config.rrf_k) for q in queries}
    passages = {d.chunk_id: d.index_text for d in docs}
    stages = measure_stages({
        "bm25_search (pool 30)": lambda q: bm25.search(q.question, config.pool, q.version_filter),
        "dense_query_embedding": lambda q: embedder.encode([q.question]),
        "dense_search incl. embedding (pool 30)":
            lambda q: dense.search(q.question, config.pool, q.version_filter),
        "rrf_fusion": lambda q: rrf_fuse({"bm25": bm_lists[q.query_id],
                                          "dense": dn_lists[q.query_id]}, config.rrf_k),
        "cross_encoder_rerank (30 candidates)":
            lambda q: rerank(q.question, fused[q.query_id][:config.rerank_pool], passages, scorer,
                             TOP_K),
    }, queries, reps=args.reps)

    ce = getattr(scorer, "_model", None)
    ce_model = ce() if callable(ce) else None
    devices = {"embedder": str(getattr(embedder._model, "device", "unknown")),
               "cross_encoder": str(getattr(ce_model, "device", "unknown"))}
    results = {
        "meta": {
            "generated_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_commit": git_commit(), "hardware": hardware(), "libraries": library_versions(),
            "devices": devices,
            "config": {"top_k": TOP_K, "rrf_k": config.rrf_k, "pool": config.pool,
                       "rerank_pool": config.rerank_pool, "embedder": DEFAULT_MODEL,
                       "reranker": DEFAULT_RERANKER, "dense_backend": resolve_backend(),
                       "dense_max_tokens": embedder.max_tokens, "latency_reps": args.reps},
            "corpus": {"n_chunks": len(docs), "n_passages": len(dense.passage_doc)},
            "dataset": dataset_summary(queries, args.questions),
        },
        "cold_start": cold,
        "latency": {"modes": latency_modes, "stages": stages,
                    "config": {"reps": args.reps, "warmup_passes": 1}},
        **quality,
    }
    text = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    (args.out_dir / "results.json").write_text(text, encoding="utf-8")
    # render from the JSON that was written, so the report always matches results.json exactly
    (args.out_dir / "report.md").write_text(render_report(json.loads(text)), encoding="utf-8")
    for m in MODES:
        o = results["modes"][m]["overall"]
        print(f"{m:14s} nDCG@5={o['ndcg@5']:.3f} MRR@10={o['mrr@10']:.3f} R@1={o['recall@1']:.3f} "
              f"R@5={o['recall@5']:.3f} R@10={o['recall@10']:.3f} Hit@5={o['hit@5']:.3f} "
              f"p50={latency_modes[m]['p50_ms']:.1f}ms p95={latency_modes[m]['p95_ms']:.1f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
