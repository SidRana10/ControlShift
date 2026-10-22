"""Benchmark runner: evaluates retrieval callables on the question set and aggregates results."""
from __future__ import annotations

import platform
import subprocess
import sys
import time
from collections.abc import Callable
from importlib import metadata

from .dataset import CATEGORIES, Query
from .metrics import (
    METRIC_NAMES,
    bootstrap_ci,
    dedupe,
    mean,
    paired_bootstrap_ci,
    percentile,
    query_metrics,
    version_isolation,
)

MODES = ["bm25", "dense", "hybrid", "hybrid_rerank"]
TOP_K = 10
SearchFn = Callable[[str, int, "str | None"], list]


def first_relevant_rank(ranking: list[str], relevance: dict[str, int]) -> int | None:
    for i, c in enumerate(dedupe(ranking), start=1):
        if relevance.get(c, 0) >= 1:
            return i
    return None


def run_mode(queries: list[Query], search: SearchFn, k: int = TOP_K) -> dict[str, dict]:
    """Per query: ranked parent chunks (graded), metrics and version isolation."""
    out = {}
    for q in queries:
        hits = search(q.question, k, q.version_filter)
        unique = _unique(hits)[:k]
        ranking = [h.chunk_id for h in unique]
        versions = [h.version for h in unique]
        rel = q.relevance
        out[q.query_id] = {
            "ranking": [{"chunk_id": h.chunk_id, "version": h.version,
                         "grade": rel.get(h.chunk_id, 0)}
                        for h in unique],
            "metrics": query_metrics(ranking, rel),
            "first_relevant_rank": first_relevant_rank(ranking, rel),
            "version_isolation": version_isolation(versions, q.version_filter),
        }
    return out


def _unique(hits: list) -> list:
    seen, out = set(), []
    for h in hits:
        if h.chunk_id not in seen:
            seen.add(h.chunk_id)
            out.append(h)
    return out


def aggregate(queries: list[Query], per_query: dict[str, dict]) -> dict:
    """Mean metrics overall (final queries only) and per category, plus provisional separately."""
    final = [q for q in queries if q.status == "final"]
    prov = [q for q in queries if q.status == "provisional"]

    def avg(qs: list[Query]) -> dict:
        return {m: mean([per_query[q.query_id]["metrics"][m] for q in qs]) for m in METRIC_NAMES} | {
            "n": len(qs)}

    iso = [per_query[q.query_id]["version_isolation"] for q in final if q.version_filter]
    out = {
        "overall": avg(final),
        "by_category": {c: avg([q for q in final if q.category == c]) for c in CATEGORIES
                        if any(q.category == c for q in final)},
        "version_isolation": {
            "queries_with_filter": len(iso),
            "mean_fraction_in_version": mean(iso) if iso else None,
            "accuracy_all_results_in_version": (sum(x == 1.0 for x in iso) / len(iso))
            if iso else None},
        "provisional": avg(prov) if prov else None,
        "ci95": {},
    }
    for m in ("ndcg@5", "mrr@10", "recall@5", "hit@5"):
        vals = [per_query[q.query_id]["metrics"][m] for q in final]
        out["ci95"][m] = list(bootstrap_ci(vals))
    return out


def paired_differences(queries: list[Query], results: dict[str, dict], base: str) -> dict:
    final = [q for q in queries if q.status == "final"]
    out = {}
    for mode in results:
        if mode == base:
            continue
        a = [results[mode][q.query_id]["metrics"]["ndcg@5"] for q in final]
        b = [results[base][q.query_id]["metrics"]["ndcg@5"] for q in final]
        lo, hi = paired_bootstrap_ci(a, b)
        out[mode] = {"vs": base, "metric": "ndcg@5", "mean_diff": mean(a) - mean(b),
                     "ci95": [lo, hi]}
    return out


def _entry(q: Query, results: dict[str, dict], modes: list[str]) -> dict:
    return {"query_id": q.query_id, "question": q.question, "category": q.category,
            "version_filter": q.version_filter,
            **{m: {"ndcg@5": results[m][q.query_id]["metrics"]["ndcg@5"],
                   "first_relevant_rank": results[m][q.query_id]["first_relevant_rank"]}
               for m in modes}}


def compare_examples(queries: list[Query], results: dict[str, dict]) -> dict:
    """Where hybrid beats / loses to the better of its two components (nDCG@5), and the same
    for the reranker versus plain hybrid. Only final queries; strict inequality."""
    final = [q for q in queries if q.status == "final"]
    out = {"hybrid_helps": [], "hybrid_hurts": [], "rerank_helps": [], "rerank_hurts": []}
    nd = lambda m, q: results[m][q.query_id]["metrics"]["ndcg@5"]
    for q in final:
        best_single, h, r = max(nd("bm25", q), nd("dense", q)), nd("hybrid", q), nd("hybrid_rerank", q)
        mods = ["bm25", "dense", "hybrid", "hybrid_rerank"]
        if h > best_single + 1e-9:
            out["hybrid_helps"].append(_entry(q, results, mods))
        elif h < best_single - 1e-9:
            out["hybrid_hurts"].append(_entry(q, results, mods))
        if r > h + 1e-9:
            out["rerank_helps"].append(_entry(q, results, mods))
        elif r < h - 1e-9:
            out["rerank_hurts"].append(_entry(q, results, mods))
    return out


def evaluate(queries: list[Query], searches: dict[str, SearchFn], k: int = TOP_K) -> dict:
    results = {m: run_mode(queries, fn, k) for m, fn in searches.items()}
    modes = {m: aggregate(queries, results[m]) for m in searches}
    out = {"modes": modes, "per_query": results}
    if "bm25" in searches:
        out["paired_vs_bm25"] = paired_differences(queries, results, "bm25")
    if {"bm25", "dense", "hybrid", "hybrid_rerank"} <= set(searches):
        out["examples"] = compare_examples(queries, results)
    return out


# ---- latency -------------------------------------------------------------------------------------
def summarize_ms(samples_s: list[float]) -> dict:
    ms = [s * 1000 for s in samples_s]
    return {"n": len(ms), "mean_ms": mean(ms), "p50_ms": percentile(ms, 50),
            "p95_ms": percentile(ms, 95), "min_ms": min(ms), "max_ms": max(ms)}


def measure_latency(queries: list[Query], searches: dict[str, SearchFn], reps: int = 5,
                    k: int = TOP_K, warmup_passes: int = 1,
                    clock: Callable[[], float] = time.perf_counter) -> dict:
    """Steady-state per-query latency. Each mode is warmed up with full passes (discarded), then
    timed over `reps` passes of every query; the order of modes is fixed and queries are never
    cached, so a repeat measures the same work."""
    out = {}
    for mode, fn in searches.items():
        for _ in range(warmup_passes):
            for q in queries:
                fn(q.question, k, q.version_filter)
        samples = []
        for _ in range(reps):
            for q in queries:
                t = clock()
                fn(q.question, k, q.version_filter)
                samples.append(clock() - t)
        out[mode] = summarize_ms(samples)
    return out


def measure_stages(stages: dict[str, Callable[[Query], object]], queries: list[Query],
                   reps: int = 5, clock: Callable[[], float] = time.perf_counter) -> dict:
    """Time named pipeline stages separately (each callable is a full stage run for one query)."""
    out = {}
    for name, fn in stages.items():
        for q in queries:  # warm-up pass
            fn(q)
        samples = []
        for _ in range(reps):
            for q in queries:
                t = clock()
                fn(q)
                samples.append(clock() - t)
        out[name] = summarize_ms(samples)
    return out


# ---- environment ---------------------------------------------------------------------------------
def library_versions() -> dict:
    out = {}
    for name in ("torch", "faiss-cpu", "sentence-transformers", "transformers", "rank-bm25",
                 "numpy", "pydantic"):
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def hardware() -> dict:
    cpu = None
    if sys.platform == "darwin":
        try:
            cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                 text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            cpu = None
    import os
    return {"platform": platform.platform(), "machine": platform.machine(), "cpu": cpu,
            "logical_cpus": os.cpu_count(), "python": sys.version.split()[0]}
