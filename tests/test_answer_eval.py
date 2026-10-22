"""Phase 5B step 2: offline grounded-answer evaluation (gold integrity, checks, review tracking)."""
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from controlshift.evaluation import answers as ans
from controlshift.evaluation.answer_report import render_answer_report, render_worksheet
from controlshift.evidence.assemble import EvidenceAssembler
from controlshift.generation.config import Settings
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.store.queries import KnowledgeStore
from controlshift.store.schema import connect
from fakes import FakeProvider

EVAL = Path(__file__).resolve().parents[1] / "eval"
ROOT = EVAL.parent


@pytest.fixture(scope="module")
def gold():
    return ans.load_gold(EVAL / "answer_questions.jsonl")


@pytest.fixture(scope="module")
def by_id(gold):
    return {g["question_id"]: g for g in gold}


@pytest.fixture(scope="module")
def conn(real_db):
    return connect(real_db[0], readonly=True)


@pytest.fixture(scope="module")
def store(real_db):
    with KnowledgeStore(real_db[0]) as s:
        yield s


@pytest.fixture(scope="module")
def assembler(store, real_db):
    return EvidenceAssembler(store, BM25Index.build(load_corpus(real_db[0])).search, "bm25")


# ---- gold dataset integrity ---------------------------------------------------------------------
def test_gold_schema_and_composition(gold):
    assert ans.validate_gold_schema(gold) == []
    assert 16 <= len(gold) <= 20
    cats = {g["category"] for g in gold}
    assert cats == set(ans.CATEGORIES)
    assert all(g["review"] == {"label_provenance": ans.PROVENANCE, "human_reviewed": False} for g in gold)
    assert sum(g["must_abstain"] for g in gold) >= 3
    assert any(g["conflict_rows"] for g in gold) and any(g["expect_new"] for g in gold)
    assert any(len(g["expected_mappings"]) >= 3 for g in gold)  # one-to-many present


def test_gold_matches_database(gold, real_db):
    assert ans.validate_gold_against_db(gold, real_db[0]) == []


def mutate(gold, qid, fn):
    g = copy.deepcopy(gold)
    fn(next(x for x in g if x["question_id"] == qid))
    return g


@pytest.mark.parametrize("qid,fn,fragment", [
    ("A01", lambda g: g["expected_facts"][0].update(quote="Totally invented text."), "quote is not in stored text"),
    ("A01", lambda g: g["expected_controls"].append({"control_id": "GV.ZZ-99", "version": "2.0"}), "not in CSF"),
    ("C01", lambda g: g["expected_mappings"][0].update(reference="ID.AM-4"), "does not match crosswalk row"),
    ("C01", lambda g: g["expected_crosswalk_rows"].append(99999), "does not exist"),
    ("F01", lambda g: g.update(conflict_rows=[g["conflict_rows"][0]]), "not a mapped+new pair"),
    ("E01", lambda g: g.update(expect_new=["GV.SC-03"]), "not purely"),
    ("G01", lambda g: g.update(forbidden_mapping_controls=["ID.AM-1"]), "expected unmapped"),
    ("H02", lambda g: g.update(absent_terms=["supply chain"]), "not absent"),
])
def test_db_validation_catches_false_expectations(gold, real_db, qid, fn, fragment):
    errors = ans.validate_gold_against_db(mutate(gold, qid, fn), real_db[0])
    assert any(fragment in e for e in errors), errors


@pytest.mark.parametrize("qid,fn,fragment", [
    ("A01", lambda g: g["review"].update(human_reviewed=True), "not human-reviewed"),
    ("A01", lambda g: g.update(category="nope"), "unknown category"),
    ("H01", lambda g: g.update(abstention_basis=None), "needs an abstention_basis"),
    ("H01", lambda g: g.update(expected_mappings=[{"row": 1}]), "must not expect mappings"),
    ("A01", lambda g: g.update(expected_facts=[], expected_controls=[]), "no expected facts"),
    ("A01", lambda g: g.pop("question"), "missing fields"),
])
def test_schema_validation_catches_problems(gold, qid, fn, fragment):
    assert any(fragment in e for e in ans.validate_gold_schema(mutate(gold, qid, fn)))


def test_duplicate_ids_and_bad_files(gold, tmp_path):
    dup = copy.deepcopy(gold)
    dup[1]["question_id"] = dup[0]["question_id"]
    assert any("duplicate" in e for e in ans.validate_gold_schema(dup))
    with pytest.raises(ans.GoldError):
        ans.load_gold(tmp_path / "none.jsonl")
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{oops\n")
    with pytest.raises(ans.GoldError):
        ans.load_gold(bad)


# ---- answer checks: valid and invalid -------------------------------------------------------------
def fixture_for(by_id, conn, qid):
    return ans.reference_fixture(by_id[qid], conn)


def failed(checks):
    return {c["name"] for c in checks if c["status"] == "fail"}


def test_reference_fixtures_pass_every_applicable_check(gold, conn):
    for g in gold:
        if g.get("invalid_input"):
            assert ans.reference_fixture(g, conn) is None  # rejected with 422, never generated
            continue
        answer, allowed = ans.reference_fixture(g, conn)
        checks = ans.check_answer(answer, g, conn, allowed)
        assert failed(checks) == set(), (g["question_id"], [c for c in checks if c["status"] == "fail"])
        assert ans.summarize_checks(checks)["semantic_faithfulness"] == ans.SEMANTIC


def test_valid_and_invalid_citations(by_id, conn):
    g = by_id["A01"]
    a, allowed = fixture_for(by_id, conn, "A01")
    fake = {**a, "citations": [*a["citations"], "chunk:csf2.0:subcategory:GV.ZZ-99"]}
    assert "citation_ids_valid" in failed(ans.check_answer(fake, g, conn, allowed))
    malformed = {**a, "citations": [*a["citations"], "banana"]}
    assert "citation_ids_valid" in failed(ans.check_answer(malformed, g, conn, allowed))
    spare = "chunk:csf2.0:subcategory:GV.OC-01"
    real_not_in_bundle = {**a, "citations": [*a["citations"], spare]}
    res = ans.check_answer(real_not_in_bundle, g, conn, allowed)
    assert "citations_in_bundle" in failed(res) and "citation_ids_valid" not in failed(res)
    assert next(c for c in ans.check_answer(a, g, conn, None) if c["name"] == "citations_in_bundle")["status"] == "n/a"


def test_incorrect_framework_version_is_flagged(by_id, conn):
    g = by_id["A02"]  # CSF 1.1 only
    a, allowed = fixture_for(by_id, conn, "A02")
    wrong = {**a, "citations": [*a["citations"], "chunk:csf2.0:subcategory:PR.AT-01"]}
    res = ans.check_answer(wrong, g, conn, allowed | {"chunk:csf2.0:subcategory:PR.AT-01"})
    assert "versions_correct" in failed(res)
    bad_dir = {**a, "mappings": [{"focal_id": "ID.BE-2", "reference_id": "GV.OC-01", "note": "",
                                  "citations": ["xwalk:row4"]}], "citations": [*a["citations"], "xwalk:row4"]}
    assert "versions_correct" in failed(ans.check_answer(bad_dir, g, conn, allowed | {"xwalk:row4"}))


def test_invented_and_miscited_mappings(by_id, conn):
    g = by_id["C01"]
    a, allowed = fixture_for(by_id, conn, "C01")
    invented = copy.deepcopy(a)
    invented["mappings"][0]["reference_id"] = "ID.AM-4"
    assert {"mapping_pairs_official", "mapping_cites_matching_row"} <= failed(ans.check_answer(invented, g, conn, allowed))
    miscited = copy.deepcopy(a)
    miscited["mappings"][0]["citations"] = ["xwalk:row5"]  # real pair, wrong row (row 4 is ID.BE-2)
    res = failed(ans.check_answer(miscited, g, conn, allowed))
    assert "mapping_cites_matching_row" in res and "mapping_pairs_official" not in res
    case_insens = copy.deepcopy(a)
    case_insens["mappings"][0]["focal_id"] = "gv.oc-01"
    assert failed(ans.check_answer(case_insens, g, conn, allowed)) == set()


def test_one_to_many_requires_every_official_row(by_id, conn):
    g = by_id["C03"]  # PR.DS-01 -> four rows
    a, allowed = fixture_for(by_id, conn, "C03")
    assert len(g["expected_crosswalk_rows"]) == 4
    short = copy.deepcopy(a)
    drop = "xwalk:row122"
    short["citations"] = [c for c in short["citations"] if c != drop]
    short["mappings"] = [m for m in short["mappings"] if drop not in m["citations"]]
    short["key_changes"] = [k for k in short["key_changes"] if drop not in k["citations"]]
    res = ans.check_answer(short, g, conn, allowed)
    assert failed(res) == {"expected_rows_covered"}
    assert "122" in next(c for c in res if c["name"] == "expected_rows_covered")["detail"]


def test_mapping_conflict_must_be_preserved(by_id, conn):
    g = by_id["F01"]
    a, allowed = fixture_for(by_id, conn, "F01")
    assert failed(ans.check_answer(a, g, conn, allowed)) == set()
    only_mapped = copy.deepcopy(a)
    only_mapped["citations"] = [c for c in only_mapped["citations"] if c != "xwalk:row26"]
    only_mapped["mappings"] = [m for m in only_mapped["mappings"] if m["reference_id"]]
    only_mapped["key_changes"] = [k for k in only_mapped["key_changes"] if "xwalk:row26" not in k["citations"]]
    only_mapped["answer"] = "GV.SC-03 maps to ID.SC-2."
    assert "conflict_preserved" in failed(ans.check_answer(only_mapped, g, conn, allowed))
    silent = copy.deepcopy(a)
    silent["answer"] = "GV.SC-03 relates to ID.SC-2 and has a new row."
    silent["uncertainties"] = []
    detail = next(c for c in ans.check_answer(silent, g, conn, allowed) if c["name"] == "conflict_preserved")
    assert detail["status"] == "fail" and "flag the disagreement" in detail["detail"]


def test_conceptually_new_control_must_not_get_a_reference(by_id, conn):
    g = by_id["E01"]
    a, allowed = fixture_for(by_id, conn, "E01")
    assert failed(ans.check_answer(a, g, conn, allowed)) == set()
    assert a["mappings"][0]["reference_id"] is None
    invented = copy.deepcopy(a)
    invented["mappings"][0]["reference_id"] = "ID.GV-1"
    assert {"new_control_no_reference", "mapping_pairs_official"} <= failed(ans.check_answer(invented, g, conn, allowed))


def test_unsupported_removal_claims_and_unmapped_controls(by_id, conn):
    g = by_id["G01"]
    a, allowed = fixture_for(by_id, conn, "G01")
    removed = {**a, "answer": a["answer"] + " RC.CO-2 was removed from CSF 2.0."}
    assert "no_unsupported_removal" in failed(ans.check_answer(removed, g, conn, allowed))
    invented_map = {**a, "mappings": [{"focal_id": "GV.OC-01", "reference_id": "RC.CO-2", "note": "",
                                       "citations": ["xwalk:row4"]}], "citations": [*a["citations"], "xwalk:row4"]}
    res = failed(ans.check_answer(invented_map, g, conn, allowed | {"xwalk:row4"}))
    assert {"no_forbidden_mappings", "mapping_pairs_official"} <= res
    # wording is allowed when a cited chunk really says it
    chunk = conn.execute("SELECT chunk_id FROM chunk WHERE lower(text) LIKE '%removed%' LIMIT 1").fetchone()
    if chunk:
        cid = f"chunk:{chunk[0]}"
        ok = {**a, "answer": "The text says something was removed.", "citations": [cid]}
        assert "no_unsupported_removal" not in failed(ans.check_answer(ok, g, conn, allowed | {cid}))


def test_missing_control_reference_and_uncited_claims(by_id, conn):
    g = by_id["A01"]
    a, allowed = fixture_for(by_id, conn, "A01")
    no_ref = {**a, "citations": [], "answer": "It requires something about suppliers.",
              "key_changes": []}
    res = failed(ans.check_answer(no_ref, g, conn, allowed))
    assert {"expected_controls_referenced", "no_uncited_claims"} <= res
    assert "no_uncited_claims" in failed(ans.check_answer(
        {**a, "key_changes": [{"statement": "x", "citations": []}]}, g, conn, allowed))


# ---- abstention and missing evidence ----------------------------------------------------------------
def test_abstention_is_required_and_not_overused(by_id, conn):
    h = by_id["H02"]
    abstain = {"answer": "", "abstained": True, "abstention_reason": "topic not in corpus"}
    assert failed(ans.check_answer(abstain, h, conn, set())) == set()
    answered = {"answer": "It requires PQC.", "citations": ["chunk:csf2.0:subcategory:GV.SC-03"]}
    assert "abstention_correct" in failed(ans.check_answer(answered, h, conn, {"chunk:csf2.0:subcategory:GV.SC-03"}))
    a = by_id["A01"]
    unneeded = ans.check_answer(abstain, a, conn, set())
    assert failed(unneeded) == {"abstention_correct"}
    assert {c["status"] for c in unneeded if c["name"] == "versions_correct"} == {"n/a"}


@pytest.mark.parametrize("bad", [["a", "list"], {"answer": 5}, {}, {"abstained": True},
                                 {"answer": "x", "citations": "not-a-list"}, None, "text"])
def test_invalid_response_structures(by_id, conn, bad):
    res = ans.check_answer(bad, by_id["A01"], conn, set())
    assert [c["name"] for c in res] == ["schema_valid"] and res[0]["status"] == "fail"


def test_missing_evidence_and_deterministic_abstention(assembler, by_id, store):
    h01 = ans.evidence_checks(assembler.assemble(by_id["H01"]["question"]), by_id["H01"], store)
    assert {c["name"]: c["status"] for c in h01}["missing_evidence_reported"] == "pass"
    h04 = {c["name"]: c["status"] for c in ans.evidence_checks(assembler.assemble("   "), by_id["H04"], store)}
    assert h04["rejected_as_invalid_request"] == "pass" and h04["defence_in_depth_if_reached"] == "pass"
    assert "deterministic_abstention" not in h04
    # sabotage: pretend the pipeline invented evidence for an unknown control
    bundle = assembler.assemble(by_id["C01"]["question"])
    bad = ans.evidence_checks(bundle, by_id["H01"], store)
    assert {c["name"]: c["status"] for c in bad}["missing_evidence_reported"] == "fail"


# ---- evidence stage ---------------------------------------------------------------------------------------
def test_evidence_stage_runs_and_detects_pipeline_regressions(gold, assembler, store, by_id):
    stage = ans.run_evidence_stage(gold, assembler, store)
    agg = stage["aggregate"]
    assert agg["n_questions"] == len(gold)
    assert agg["per_check"]["bundle_citations_structurally_valid"]["failed"] == 0
    assert agg["per_check"]["conflict_surfaced"]["applicable"] == 2
    bundle = assembler.assemble(by_id["F01"]["question"])
    bundle.conflicts = []  # simulate losing the conflict flag
    assert {c["name"]: c["status"] for c in ans.evidence_checks(bundle, by_id["F01"], store)}["conflict_surfaced"] == "fail"
    leaky = assembler.assemble(by_id["A02"]["question"])
    leaky.passages.append({**leaky.passages[0], "version": "2.0"})
    assert {c["name"]: c["status"] for c in ans.evidence_checks(leaky, by_id["A02"], store)}["version_isolation"] == "fail"
    assert {c["name"]: c["status"] for c in ans.evidence_checks(
        assembler.assemble(by_id["A03"]["question"]), by_id["A03"], store)}["expected_uncertainty_surfaced"] == "pass"


def test_aggregate_metric_calculation():
    def pq(cat, *statuses):
        checks = [{"name": f"c{i}", "level": "x", "status": s, "detail": ""} for i, s in enumerate(statuses)]
        return {"category": cat, "checks": checks, "all_passed": all(s != "fail" for s in statuses)}

    agg = ans.aggregate({"Q1": pq("a", "pass", "pass"), "Q2": pq("a", "pass", "fail"),
                         "Q3": pq("b", "n/a", "pass")})
    assert agg["n_questions"] == 3 and agg["questions_all_checks_passed"] == 2
    assert agg["per_check"]["c0"] == {"applicable": 2, "passed": 2, "failed": 0, "pass_rate": 1.0}
    assert agg["per_check"]["c1"]["pass_rate"] == pytest.approx(2 / 3)
    assert agg["per_category"] == {"a": {"questions": 2, "all_passed": 1}, "b": {"questions": 1, "all_passed": 1}}
    assert agg["failed_questions"] == ["Q2"]


# ---- validator self-test ---------------------------------------------------------------------------------------
def test_validator_self_test_accepts_fixtures_and_detects_every_injected_defect(gold, conn):
    st = ans.validator_self_test(gold, conn)
    answerable = sum(not g.get("invalid_input") for g in gold)
    assert st["fixtures_built"] == st["fixtures_accepted"] == answerable and not st["fixture_failures"]
    names = {c["name"] for c in ans.corruptions(conn)}
    assert set(st["corruptions"]) == names                     # every defect type was applicable somewhere
    for name, v in st["corruptions"].items():
        assert v["applicable"] > 0 and v["detected"] == v["applicable"] and not v["missed"], name
    assert "not any model" in st["scope"]


# ---- live mode plumbing (fake provider => never reported as a live model) --------------------------------------
def test_run_live_labels_fake_provider_and_never_claims_live_accuracy(gold, assembler, store, conn):
    g = {x["question_id"]: x for x in gold}
    answer, _ = ans.reference_fixture(g["A01"], conn)
    out = ans.run_live([g["A01"], g["H04"]], assembler, store, FakeProvider(answer), Settings(), limit=2)
    assert out["is_live_model"] is False and out["provider"] == "fake"
    assert out["per_question"]["A01"]["status"] == "answered" and out["per_question"]["A01"]["all_passed"]
    assert out["per_question"]["H04"]["status"] == "rejected_before_pipeline"  # API 422, no model call
    assert provider_calls_zero_for_h04(out)
    assert out["semantic_faithfulness"] == ans.SEMANTIC
    none = ans.run_live([g["A01"]], assembler, store, None, Settings(), limit=1)
    assert none["per_question"]["A01"]["status"] == "evidence_only" and none["per_question"]["A01"]["checks"] == []


def provider_calls_zero_for_h04(out):
    return out["per_question"]["H04"]["attempts"] == 0 and out["per_question"]["H04"]["checks"] == []


def test_live_mode_is_disabled_by_default():
    env = {k: v for k, v in os.environ.items() if k != "RUN_LIVE_LLM_EVAL"}
    r = subprocess.run([sys.executable, str(EVAL / "answer_eval.py"), "--live"], capture_output=True,
                       text=True, env=env, cwd=ROOT, check=False)
    assert r.returncode == 2 and "RUN_LIVE_LLM_EVAL=1" in r.stderr


# ---- review status tracking -----------------------------------------------------------------------------------------
def test_review_validation_and_summary(tmp_path):
    ids = ["Q1", "Q2", "Q3"]
    path = tmp_path / "r.json"
    reviews = ans.load_reviews(path, ids)
    assert all(r == ans.blank_review() for r in reviews.values())
    assert ans.review_summary(reviews) == {"total": 3, "pending": 3, "reviewed": 0,
                                           "groundedness": {}, "completeness": {}}
    done = {**ans.blank_review(), "status": "reviewed", "groundedness": "grounded",
            "completeness": "partial", "reviewer": "R. Reviewer", "notes": "ok"}
    path.write_text(json.dumps({"Q1": done}))
    loaded = ans.load_reviews(path, [*ids, "Q4"])         # existing input kept, new question pending
    assert loaded["Q1"] == done and loaded["Q4"]["status"] == "pending"
    s = ans.review_summary(loaded)
    assert (s["reviewed"], s["pending"]) == (1, 3) and s["groundedness"] == {"grounded": 1}


@pytest.mark.parametrize("patch", [
    {"status": "done"}, {"status": "reviewed"},
    {"status": "reviewed", "groundedness": "great", "completeness": "complete", "reviewer": "x"},
    {"status": "reviewed", "groundedness": "grounded", "completeness": "meh", "reviewer": "x"},
    {"status": "reviewed", "groundedness": "grounded", "completeness": "complete"},
    {"status": "pending", "groundedness": "grounded"},
])
def test_invalid_review_entries_are_rejected(patch):
    with pytest.raises(ans.ReviewError):
        ans.validate_review({**ans.blank_review(), **patch})


def test_worksheet_leaves_subjective_fields_pending_until_reviewed(gold, assembler, store, conn):
    res = {"evidence_stage": ans.run_evidence_stage(gold[:2], assembler, store)}
    reviews = {g["question_id"]: ans.blank_review() for g in gold[:2]}
    text = render_worksheet(gold[:2], res, reviews)
    assert text.count("Groundedness: PENDING") == 2 and text.count("Completeness: PENDING") == 2
    assert text.count("Human review status: **pending**") == 2
    assert "Not generated - offline mode" in text and "not human-reviewed" in text
    reviews["A01"] = {**ans.blank_review(), "status": "reviewed", "groundedness": "grounded",
                      "completeness": "complete", "reviewer": "R", "notes": "fine"}
    again = render_worksheet(gold[:2], res, reviews)
    assert "Groundedness: GROUNDED" in again and again.count("Groundedness: PENDING") == 1
    answer, _ = ans.reference_fixture(gold[0], conn)
    gen = {"A01": {"answer": {**answer, "mappings": [], "key_changes": []}, "checks": []}}
    assert answer["answer"][:20] in render_worksheet(gold[:2], res, reviews, gen)


# ---- reports are reproducible and honest ----------------------------------------------------------------------------------
def build_results(gold, assembler, store, conn):
    return {"meta": {"n_questions": len(gold), "retrieval": "bm25", "gold_sha256": "ab" * 32,
                     "by_category": {}, "human_reviewed_labels": False, "mode": "offline"},
            "evidence_stage": ans.run_evidence_stage(gold, assembler, store),
            "validator_self_test": ans.validator_self_test(gold, conn),
            "semantic_faithfulness": "requires_human_review (not evaluated)"}


def test_results_and_report_are_reproducible(gold, assembler, store, conn):
    a = json.dumps(build_results(gold, assembler, store, conn), sort_keys=True)
    b = json.dumps(build_results(gold, assembler, store, conn), sort_keys=True)
    assert a == b
    reviews = {g["question_id"]: ans.blank_review() for g in gold}
    r1 = render_answer_report(json.loads(a), reviews)
    assert r1 == render_answer_report(json.loads(b), reviews)
    for needle in ("No language model", "not human-reviewed", "Semantic faithfulness", "human reviewer",
                   "Passing structural and deterministic checks does **not** show", "Not run. Live mode is disabled"):
        assert needle in r1, needle
    assert "Reviewed: 0 /" in r1


def test_committed_artifacts_are_consistent(gold):
    results_p = EVAL / "answer_results.json"
    if not results_p.is_file():
        pytest.skip("answer evaluation not run yet")
    res = json.loads(results_p.read_text())
    assert res["meta"]["mode"] == "offline" and "live" not in res
    assert res["meta"]["gold_sha256"] == hashlib.sha256((EVAL / "answer_questions.jsonl").read_bytes()).hexdigest()
    reviews = ans.load_reviews(EVAL / "answer_review.json", [g["question_id"] for g in gold])
    assert (EVAL / "answer_report.md").read_text() == render_answer_report(res, reviews)
    assert (EVAL / "answer_review_worksheet.md").read_text() == render_worksheet(gold, res, reviews)
    assert not (EVAL / "answer_results_live.json").exists()


# ---- invalid input (API 422) is not an evidence-based abstention -----------------------------------------------------------
def test_blank_input_is_classified_as_invalid_input_not_abstention(by_id, conn):
    h04 = by_id["H04"]
    assert h04["category"] == "invalid_input" and h04["invalid_input"] is True
    assert h04["expected_api_status"] == 422 and h04["must_abstain"] is False and not h04["abstention_basis"]
    assert all(g["category"] != "abstention" or g["must_abstain"] for g in by_id.values())
    assert {g["question_id"] for g in by_id.values() if g["category"] == "abstention"} == {"H01", "H02", "H03"}
    res = ans.check_answer({"answer": "x"}, h04, conn, set())
    assert [c["status"] for c in res] == ["n/a"]


def test_the_real_api_models_reject_what_the_gold_calls_invalid(by_id):
    from pydantic import ValidationError

    from controlshift.api.schemas import AskRequest, CompareRequest
    for model in (AskRequest, CompareRequest):
        with pytest.raises(ValidationError):
            model(question=by_id["H04"]["question"])
    AskRequest(question=by_id["H02"]["question"])    # evidence-based abstention cases ARE valid requests
    AskRequest(question=by_id["H03"]["question"])


@pytest.mark.parametrize("fn,fragment", [
    (lambda g: g.update(category="abstention"), "invalid input must be category invalid_input"),
    (lambda g: g.update(must_abstain=True, abstention_basis="evidence_absent"), "not an evidence-based abstention"),
    (lambda g: g.update(expected_api_status=200), "expect HTTP 422"),
])
def test_invalid_input_schema_rules(gold, fn, fragment):
    assert any(fragment in e for e in ans.validate_gold_schema(mutate(gold, "H04", fn))), fragment


def test_valid_question_cannot_be_labelled_invalid_and_abstention_needs_evidence_basis(gold):
    assert any("requires invalid_input=true" in e for e in ans.validate_gold_schema(
        mutate(gold, "A01", lambda g: g.update(category="invalid_input"))))
    assert any("needs must_abstain and a basis" in e for e in ans.validate_gold_schema(
        mutate(gold, "H01", lambda g: g.update(abstention_basis="unsupported_question"))))


def test_topic_absent_abstentions_rest_on_concept_terms_not_one_keyword(by_id, gold, real_db, conn):
    for qid in ("H02", "H03"):
        g = by_id[qid]
        assert len(set(g["absent_terms"])) >= 3 and g["abstention_justification"].strip()
        for term in g["absent_terms"]:   # re-verified here, directly against the stored text
            n = conn.execute("SELECT COUNT(*) FROM chunk WHERE lower(text) LIKE ?", (f"%{term}%",)).fetchone()[0]
            assert n == 0, (qid, term)
    assert "cryptograph" in by_id["H02"]["absent_terms"] and "quantum" in by_id["H02"]["absent_terms"]
    assert {"penalt", "sanction", "consequence"} <= set(by_id["H03"]["absent_terms"])
    # closest related passages were read and recorded; counts must stay in sync with the corpus
    assert set(by_id["H03"]["reviewed_related_terms"]) >= {"compliance", "voluntary"}
    assert ans.validate_gold_against_db(gold, real_db[0]) == []
    one_keyword = mutate(gold, "H02", lambda g: g.update(absent_terms=["quantum"]))
    assert any("topic_absent needs >=3" in e for e in ans.validate_gold_schema(one_keyword))
    no_why = mutate(gold, "H03", lambda g: g.update(abstention_justification=""))
    assert any("written justification" in e for e in ans.validate_gold_schema(no_why))
    drift = mutate(gold, "H03", lambda g: g["reviewed_related_terms"]["compliance"].update(chunks=99))
    assert any("related term 'compliance'" in e for e in ans.validate_gold_against_db(drift, real_db[0]))
    unreviewed = mutate(gold, "H03", lambda g: g["reviewed_related_terms"]["voluntary"].update(note=""))
    assert any("review note is missing" in e for e in ans.validate_gold_against_db(unreviewed, real_db[0]))


def test_report_describes_offline_pass_rate_as_regression_validation_not_model_accuracy(gold, assembler, store, conn):
    res = build_results(gold, assembler, store, conn)
    text = render_answer_report(json.loads(json.dumps(res)), {g["question_id"]: ans.blank_review() for g in gold})
    assert "regression validation of the deterministic pipeline - not live-model answer accuracy" in text
    assert "invalid_input" in text and "HTTP 422" in text and "not an abstention" in text
    assert "No live answer accuracy is reported here" in text
