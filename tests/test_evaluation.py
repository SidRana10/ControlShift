"""Phase 5A: metrics, dataset integrity, aggregation, latency helpers and report generation."""
import copy
import json
import math
import re
from pathlib import Path

import pytest

from controlshift.evaluation import dataset as ds
from controlshift.evaluation import metrics as mt
from controlshift.evaluation.report import render_report
from controlshift.evaluation.runner import (
    aggregate,
    evaluate,
    measure_latency,
    measure_stages,
    run_mode,
    summarize_ms,
)
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.retrieval.hits import Hit
from controlshift.store.schema import connect

EVAL = Path(__file__).resolve().parents[1] / "eval"


# ---- metric definitions (hand-computed expectations) -----------------------------------------
REL = {"a": 2, "b": 1, "c": 1}


def test_recall_at_k_with_multiple_relevant():
    ranking = ["x", "a", "y", "b", "z"]
    assert mt.recall_at_k(ranking, REL, 1) == 0.0
    assert mt.recall_at_k(ranking, REL, 2) == pytest.approx(1 / 3)
    assert mt.recall_at_k(ranking, REL, 5) == pytest.approx(2 / 3)
    assert mt.recall_at_k(["a", "b", "c"], REL, 3) == 1.0


def test_hit_rate_and_mrr():
    assert mt.hit_rate_at_k(["x", "y", "b"], REL, 5) == 1.0
    assert mt.hit_rate_at_k(["x", "y", "b"], REL, 2) == 0.0
    assert mt.reciprocal_rank_at_k(["x", "y", "b"], REL, 10) == pytest.approx(1 / 3)
    assert mt.reciprocal_rank_at_k(["x1", "x2", "x3", "a"], REL, 3) == 0.0  # first relevant beyond cut-off
    assert mt.reciprocal_rank_at_k(["a"], REL, 10) == 1.0


def test_ndcg_graded_matches_formula():
    rel = {"a": 2, "b": 1}
    dcg = 1 / math.log2(2) + 3 / math.log2(3)          # b (gain 1) at rank 1, a (gain 3) at rank 2
    ideal = 3 / math.log2(2) + 1 / math.log2(3)        # a then b
    assert mt.ndcg_at_k(["b", "a"], rel, 5) == pytest.approx(dcg / ideal)
    assert mt.ndcg_at_k(["a", "b"], rel, 5) == pytest.approx(1.0)
    assert mt.ndcg_at_k(["a", "b", "x"], rel, 1) == pytest.approx(1.0)  # ideal is cut at k too
    assert mt.ndcg_at_k(["x", "y"], rel, 5) == 0.0


def test_no_relevant_result_retrieved_scores_zero_everywhere():
    m = mt.query_metrics(["x", "y", "z"], REL)
    assert set(m) == set(mt.METRIC_NAMES) and all(v == 0.0 for v in m.values())
    assert all(v == 0.0 for v in mt.query_metrics([], REL).values())


def test_repeated_result_ids_count_once_at_first_position():
    ranking = ["a", "a", "a", "x", "b"]
    assert mt.dedupe(ranking) == ["a", "x", "b"]
    assert mt.recall_at_k(ranking, {"a": 1, "b": 1}, 3) == 1.0  # b is 3rd after dedupe
    assert mt.reciprocal_rank_at_k(["x", "b", "b"], {"b": 1}, 10) == 0.5
    assert mt.ndcg_at_k(["a", "a"], {"a": 1}, 5) == pytest.approx(1.0)


def test_metrics_require_a_relevant_label():
    with pytest.raises(ValueError):
        mt.recall_at_k(["a"], {}, 5)
    with pytest.raises(ValueError):
        mt.ndcg_at_k(["a"], {"a": 0}, 5)


def test_version_isolation_metric():
    assert mt.version_isolation(["2.0", "2.0"], "2.0") == 1.0
    assert mt.version_isolation(["2.0", "1.1"], "2.0") == 0.5
    assert mt.version_isolation([], "2.0") == 1.0
    assert mt.version_isolation(["1.1"], None) is None


def test_bootstrap_and_percentiles_are_deterministic():
    vals = [0.0, 1.0, 1.0, 0.5, 0.25, 1.0]
    lo, hi = mt.bootstrap_ci(vals)
    assert (lo, hi) == mt.bootstrap_ci(vals) and lo <= mt.mean(vals) <= hi
    assert mt.bootstrap_ci([0.7] * 5) == (0.7, 0.7)
    assert mt.paired_bootstrap_ci(vals, vals)[0] == 0.0
    assert mt.percentile([1, 2, 3, 4], 50) == 2.5 and mt.percentile([5], 95) == 5
    assert mt.percentile(list(range(101)), 95) == pytest.approx(95)


# ---- dataset: schema and label integrity ---------------------------------------------------------
@pytest.fixture(scope="module")
def questions():
    return ds.load_questions(EVAL / "questions.jsonl")


def test_real_dataset_schema_and_composition(questions):
    assert ds.validate_schema(questions) == []
    assert 30 <= len(questions) <= 40
    cats = {c: sum(q.category == c for q in questions) for c in ds.CATEGORIES}
    assert all(n >= 5 for n in cats.values()), cats
    assert any(q.version_filter for q in questions) and any(not q.version_filter for q in questions)
    assert {q.difficulty for q in questions} == set(ds.DIFFICULTIES)
    assert any(q.status == "provisional" for q in questions)
    assert all(q.human_reviewed is False and q.label_provenance == ds.PROVENANCE for q in questions)


def test_real_labels_match_the_database(questions, real_db):
    assert ds.validate_against_db(questions, real_db[0]) == []


def test_crosswalk_justified_labels_cite_real_rows_that_involve_the_chunk(questions, real_db):
    conn = connect(real_db[0], readonly=True)
    checked = 0
    for q in questions:
        for r in q.relevant:
            m = re.search(r"crosswalk rows? ([\d, \-]+)", r.why)
            if not m:
                continue
            rows = [int(x) for x in re.findall(r"\d+", m.group(1))]
            eid = conn.execute("SELECT element_id FROM chunk WHERE chunk_id=?",
                               (r.chunk_id,)).fetchone()[0]
            hits = conn.execute(
                f"SELECT COUNT(*) FROM crosswalk_mapping WHERE excel_row IN ({','.join('?' * len(rows))})"
                " AND (focal_element_id=? OR reference_element_id=?)", (*rows, eid, eid)).fetchone()[0]
            assert hits >= 1, f"{q.query_id}/{r.chunk_id}: cited rows {rows} do not involve {eid}"
            checked += 1
    assert checked >= 15


def mutate(questions, fn):
    qs = copy.deepcopy(questions)
    fn(qs)
    return qs


@pytest.mark.parametrize("name,fn,fragment", [
    ("dup id", lambda qs: setattr(qs[1], "query_id", qs[0].query_id), "duplicate query_id"),
    ("bad category", lambda qs: setattr(qs[0], "category", "nope"), "unknown category"),
    ("bad filter", lambda qs: setattr(qs[0], "version_filter", "3.0"), "bad version_filter"),
    ("no relevant", lambda qs: setattr(qs[0], "relevant", []), "no relevant chunks"),
    ("bad grade", lambda qs: setattr(qs[0].relevant[0], "grade", 5), "grade must be 1 or 2"),
    ("no why", lambda qs: setattr(qs[0].relevant[0], "why", " "), "missing relevance explanation"),
    ("outside filter", lambda qs: setattr(qs[0].relevant[0], "version", "1.1"), "outside the version filter"),
    ("human flag lie", lambda qs: setattr(qs[0], "human_reviewed", True), "human_reviewed"),
    ("empty question", lambda qs: setattr(qs[0], "question", ""), "empty question"),
])
def test_schema_validation_catches_problems(questions, name, fn, fragment):
    qs = mutate(questions, fn)
    assert any(fragment in e for e in ds.validate_schema(qs)), name


@pytest.mark.parametrize("field,value,fragment", [
    ("chunk_id", "csf2.0:subcategory:GV.ZZ-99", "does not exist"),
    ("page", 999, "page is 999"),
    ("source_file", "other.pdf", "source_file"),
    ("section", "Wrong", "section"),
    ("control_id", "GV.SC-04", "control_id"),
    ("source_excerpt", "this is not the text", "source_excerpt"),
])
def test_db_validation_catches_label_corruption(questions, real_db, field, value, fragment):
    qs = mutate(questions, lambda qs: setattr(qs[0].relevant[0], field, value))
    assert any(fragment in e for e in ds.validate_against_db(qs, real_db[0]))


def test_final_query_needs_a_grade2_chunk(questions):
    qs = mutate(questions, lambda qs: [setattr(r, "grade", 1) for r in qs[0].relevant])
    assert any("grade-2" in e for e in ds.validate_schema(qs))


def test_loading_bad_files(tmp_path):
    with pytest.raises(ds.DatasetError):
        ds.load_questions(tmp_path / "missing.jsonl")
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n")
    with pytest.raises(ds.DatasetError, match="invalid JSON"):
        ds.load_questions(bad)
    bad.write_text('{"query_id": "x"}\n')
    with pytest.raises(ds.DatasetError, match="malformed"):
        ds.load_questions(bad)


# ---- runner / aggregation --------------------------------------------------------------------------
def mk_hit(cid, version="2.0"):
    return Hit(rank=1, score=1.0, mode="fake", chunk_id=cid, version=version, control_id=None,
               chunk_type="text", source_file="f", page=1, printed_page=None, section="s", text="t")


def tiny_queries():
    def q(qid, cat, rel, vf=None, status="final"):
        return ds.Query(qid, f"question {qid}", cat, "easy", vf, status, ds.PROVENANCE, False,
                        [ds.Relevant(c, g, "2.0", None, "f", 1, "s", "x", "why") for c, g in rel])
    return [q("A", "exact_id", [("a", 2)], "2.0"), q("B", "semantic", [("b", 2), ("c", 1)]),
            q("C", "semantic", [("d", 2)], status="provisional")]


def test_run_mode_scores_dedupes_and_checks_versions():
    qs = tiny_queries()
    data = {"A": [mk_hit("x"), mk_hit("a"), mk_hit("a"), mk_hit("y", "1.1")],
            "B": [mk_hit("c"), mk_hit("b")], "C": []}
    out = run_mode(qs, lambda text, k, v: data[text.split()[-1]], k=10)
    a = out["A"]
    assert [r["chunk_id"] for r in a["ranking"]] == ["x", "a", "y"]      # repeated 'a' removed
    assert a["first_relevant_rank"] == 2 and a["metrics"]["mrr@10"] == 0.5
    assert a["version_isolation"] == pytest.approx(2 / 3)                # one result from 1.1
    assert out["B"]["metrics"]["recall@1"] == 0.5 and out["B"]["version_isolation"] is None
    assert out["C"]["metrics"]["recall@10"] == 0.0                       # empty result list


def test_aggregation_excludes_provisional_from_headline_and_splits_categories():
    qs = tiny_queries()
    perfect = {"A": [mk_hit("a")], "B": [mk_hit("b"), mk_hit("c")], "C": [mk_hit("zzz")]}
    per_query = run_mode(qs, lambda t, k, v: perfect[t.split()[-1]])
    agg = aggregate(qs, per_query)
    assert agg["overall"]["n"] == 2 and agg["overall"]["ndcg@5"] == 1.0
    assert agg["provisional"]["n"] == 1 and agg["provisional"]["ndcg@5"] == 0.0
    assert set(agg["by_category"]) == {"exact_id", "semantic"}
    assert agg["by_category"]["semantic"]["n"] == 1
    assert agg["version_isolation"]["queries_with_filter"] == 1
    assert agg["version_isolation"]["accuracy_all_results_in_version"] == 1.0


def test_real_bm25_run_is_deterministic_and_respects_filters(questions, real_db):
    bm25 = BM25Index.build(load_corpus(real_db[0]))
    first, second = run_mode(questions, bm25.search), run_mode(questions, bm25.search)
    assert first == second
    for q in questions:
        if q.version_filter:
            assert first[q.query_id]["version_isolation"] == 1.0


def test_published_results_reproduce_for_bm25(questions, real_db):
    """eval/results.json (if present) must match a fresh BM25 run exactly: quality metrics are
    deterministic. Dense/hybrid need the models and are reproduced by eval/benchmark.py."""
    path = EVAL / "results.json"
    if not path.is_file():
        pytest.skip("eval/results.json not generated yet")
    published = json.loads(path.read_text())
    bm25 = BM25Index.build(load_corpus(real_db[0]))
    fresh = run_mode(questions, bm25.search)
    for qid, row in fresh.items():
        assert row["metrics"] == pytest.approx(published["per_query"]["bm25"][qid]["metrics"])
    assert aggregate(questions, fresh)["overall"] == pytest.approx(published["modes"]["bm25"]["overall"])


# ---- latency helpers -------------------------------------------------------------------------------------
def test_latency_summary_uses_warmup_and_reps():
    ticks = iter(range(10_000))
    calls = []
    qs = tiny_queries()

    def search(text, k, v):
        calls.append(text)
        return []

    out = measure_latency(qs, {"m": search}, reps=3, warmup_passes=2, clock=lambda: next(ticks) / 1000)
    assert len(calls) == (2 + 3) * len(qs)                 # warm-up passes are executed but not timed
    assert out["m"]["n"] == 3 * len(qs) and out["m"]["p50_ms"] == pytest.approx(1.0)
    s = summarize_ms([0.001, 0.002, 0.003, 0.004])
    assert s["mean_ms"] == pytest.approx(2.5) and s["p50_ms"] == pytest.approx(2.5)
    stage = measure_stages({"s": lambda q: None}, qs, reps=2, clock=lambda: next(ticks) / 1000)
    assert stage["s"]["n"] == 2 * len(qs)


# ---- report generation -----------------------------------------------------------------------------------------
def fake_results():
    qs = tiny_queries() + [
        ds.Query("D", "question D", "cross_version", "hard", None, "final", ds.PROVENANCE, False,
                 [ds.Relevant("d", 2, "2.0", None, "f", 1, "s", "x", "why")]),
        ds.Query("E", "question E", "version_specific", "medium", "2.0", "final", ds.PROVENANCE,
                 False, [ds.Relevant("e", 2, "2.0", None, "f", 1, "s", "x", "why")])]
    data = {
        "bm25": {"A": ["a"], "B": ["b"], "C": ["d"], "D": ["x", "d"], "E": ["e"]},
        "dense": {"A": ["x"], "B": ["c"], "C": [], "D": ["d"], "E": ["x"]},
        "hybrid": {"A": ["a"], "B": ["c", "b"], "C": ["d"], "D": ["d"], "E": ["x", "e"]},
        "hybrid_rerank": {"A": ["a"], "B": ["b", "c"], "C": ["d"], "D": ["d"], "E": ["e"]},
    }
    searches = {m: (lambda t, k, v, m=m: [mk_hit(c) for c in data[m][t.split()[-1]]]) for m in data}
    res = evaluate(qs, searches)
    lat = measure_latency(qs, searches, reps=2, clock=iter(x / 1000 for x in range(10**6)).__next__)
    res.update({
        "latency": {"modes": lat, "stages": measure_stages({"stage": lambda q: None}, qs, reps=1),
                    "config": {"reps": 2, "warmup_passes": 1}},
        "cold_start": {"load_corpus_from_sqlite": 0.5},
        "meta": {"config": {"top_k": 10, "pool": 30, "rrf_k": 60, "rerank_pool": 30,
                            "reranker": "rr", "embedder": "em", "dense_backend": "numpy"},
                 "corpus": {"n_chunks": 5, "n_passages": 6},
                 "dataset": {"n_total": 5, "n_final": 4, "n_provisional": 1, "sha256": "ab" * 32,
                             "by_category": {"exact_id": 1, "semantic": 2, "cross_version": 1,
                                             "version_specific": 1},
                             "by_difficulty": {"easy": 3, "hard": 1, "medium": 1}, "n_filtered": 2,
                             "mean_relevant": 1.2, "n_grade2": 5, "n_grade1": 1},
                 "hardware": {"cpu": "test"}, "libraries": {}, "devices": {}, "git_commit": None,
                 "generated_utc": "2000-01-01T00:00:00Z"}})
    return res


def test_report_contains_every_required_section_and_real_numbers():
    res = fake_results()
    text = render_report(res)
    for heading in ("Methodology", "Dataset composition", "Relevance-label provenance",
                    "Metric definitions", "Overall results", "Per-category performance", "Latency",
                    "Where hybrid RRF helps", "Where hybrid RRF performs worse",
                    "Known limitations and threats to validity"):
        assert heading in text, heading
    assert "not human-reviewed" in text and "No human has reviewed" in text
    for mode_label in ("BM25", "Dense", "Hybrid RRF", "Hybrid RRF + cross-encoder"):
        assert mode_label in text
    bm25_ndcg = res["modes"]["bm25"]["overall"]["ndcg@5"]
    assert f"{bm25_ndcg:.3f}" in text
    ex = res["examples"]
    assert {e["query_id"] for e in ex["hybrid_helps"]} == {"E"} or ex["hybrid_helps"] == []
    assert any(e["query_id"] == "E" for e in ex["hybrid_hurts"] + ex["hybrid_helps"])
    assert render_report(res) == text                       # deterministic
    assert "Provisional" in text


def test_committed_report_is_in_sync_with_committed_results():
    path = EVAL / "results.json"
    if not path.is_file() or not (EVAL / "report.md").is_file():
        pytest.skip("benchmark has not been run")
    assert render_report(json.loads(path.read_text())) == (EVAL / "report.md").read_text()
