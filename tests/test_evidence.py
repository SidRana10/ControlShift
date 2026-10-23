"""Evidence assembly + structural citation validation over the real NIST corpus (BM25 retrieval,
no models needed)."""
import json

import pytest

from controlshift.evidence.assemble import (
    NEW_REASON,
    NO_REF_REASON,
    EvidenceAssembler,
    validate_bundle,
)
from controlshift.evidence.citations import (
    CitationClaim,
    chunk_citation_id,
    validate_citations,
    xwalk_citation_id,
)
from controlshift.evidence.cli import main
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.retrieval.persist import build_bm25
from controlshift.store.queries import KnowledgeStore
from controlshift.store.schema import connect


@pytest.fixture(scope="module")
def store(real_db):
    with KnowledgeStore(real_db[0]) as s:
        yield s


@pytest.fixture(scope="module")
def assembler(store, real_db):
    bm25 = BM25Index.build(load_corpus(real_db[0]))
    return EvidenceAssembler(store, bm25.search, "bm25")


def ids(items, key="citation_id"):
    return [i[key] for i in items]


# ---- single-version and exact lookup --------------------------------------------------------
def test_single_version_question_is_isolated_to_that_version(assembler):
    b = assembler.assemble("What does CSF 1.1 say about data at rest?")
    assert b.query_type == "single_version" and b.searched_versions == ["1.1"]
    assert b.passages and {p["version"] for p in b.passages} == {"1.1"}
    assert {c["version"] for c in b.citations.values() if c["kind"] == "chunk"} == {"1.1"}
    assert b.crosswalk_records == [] and b.unresolved_questions == []


def test_version_isolation_for_other_version(assembler):
    b = assembler.assemble("What does CSF 2.0 say about incident response?")
    assert b.searched_versions == ["2.0"] and {p["version"] for p in b.passages} == {"2.0"}


def test_exact_control_lookup_uses_the_database_not_similarity(assembler):
    b = assembler.assemble("What does GV.SC-03 require?")
    assert b.control_ids == ["GV.SC-03"] and b.searched_versions == ["2.0"]
    rec = b.control_records[0]
    assert (rec["version"], rec["control_id"], rec["level"]) == ("2.0", "GV.SC-03", "subcategory")
    assert rec["text"].startswith("GV.SC-03: Cybersecurity supply chain risk management is integrated")
    assert rec["source_file"] == "nist_csf_2_0.pdf" and rec["page"] == 22 and rec["section"]
    assert rec["citation_id"] == "chunk:csf2.0:subcategory:GV.SC-03"
    assert b.unresolved_questions == [] and b.crosswalk_records == []  # lookup, not mapping


def test_control_in_both_versions_is_reported_for_both_with_uncertainty(assembler):
    b = assembler.assemble("What does PR.AT-1 require?")
    assert {(r["version"], r["control_id"]) for r in b.control_records} == {
        ("1.1", "PR.AT-1"), ("2.0", "PR.AT-01")}
    assert any("exists in both CSF versions" in u for u in b.unresolved_questions)
    one = assembler.assemble("What does PR.AT-1 require in CSF 1.1?")
    assert [(r["version"], r["control_id"]) for r in one.control_records] == [("1.1", "PR.AT-1")]
    assert one.searched_versions == ["1.1"] and one.unresolved_questions == []


def test_named_version_without_that_control_is_missing_not_substituted(assembler):
    b = assembler.assemble("What does GV.SC-03 require in CSF 1.1?")
    assert b.control_records == []  # nothing silently swapped in from 2.0
    assert b.missing_evidence[0]["kind"] == "control_not_found"
    assert any("exists in CSF 2.0" in u for u in b.unresolved_questions)


# ---- official mappings -------------------------------------------------------------------------
def test_one_to_many_forward_mapping(assembler):
    b = assembler.assemble("How does GV.OC-01 map to CSF 1.1?")
    assert b.query_type == "control_mapping"
    assert [(r["excel_row"], r["focal_id"], r["reference_id"]) for r in b.crosswalk_records] == [
        (4, "GV.OC-01", "ID.BE-2"), (5, "GV.OC-01", "ID.BE-3")]
    assert {(r["version"], r["control_id"]) for r in b.control_records} == {
        ("2.0", "GV.OC-01"), ("1.1", "ID.BE-2"), ("1.1", "ID.BE-3")}
    assert b.conflicts == [] and b.unmapped_controls == []
    assert all(r["direction"].startswith("CSF 2.0") for r in b.crosswalk_records)


def test_reverse_relationship_comes_from_stored_rows(assembler, store):
    b = assembler.assemble("Which CSF 2.0 controls correspond to ID.BE-2?")
    assert b.control_ids == ["ID.BE-02"]
    assert 4 in {r["excel_row"] for r in b.crosswalk_records}
    assert ("2.0", "GV.OC-01") in {(r["version"], r["control_id"]) for r in b.control_records}
    for r in b.crosswalk_records:  # every reported row is an official stored row
        assert store.mappings_2_0_to_1_1(r["focal_id"])
    many = assembler.assemble("Which CSF 2.0 controls correspond to ID.SC-1?")
    assert len(many.crosswalk_records) >= 3  # many-to-one on the 2.0 side


def test_conceptually_new_element_is_unmapped_and_nothing_is_invented(assembler):
    b = assembler.assemble("How does GV.OV-01 map to CSF 1.1?")
    assert len(b.crosswalk_records) == 1
    row = b.crosswalk_records[0]
    assert row["mapping_type"] == "new_in_2_0" and row["reference_id"] is None
    assert row["comments"] == "Conceptually new in 2.0"
    assert b.unmapped_controls == [{"control_id": "GV.OV-01", "version": "2.0",
                                    "reason": NEW_REASON, "citations": [row["citation_id"]]}]
    assert [r["version"] for r in b.control_records] == ["2.0"]  # no 1.1 counterpart fabricated
    assert b.conflicts == []


def test_conflicting_mapped_and_new_records_are_both_preserved(assembler):
    b = assembler.assemble("How does GV.SC-03 map to CSF 1.1?")
    assert [(r["excel_row"], r["mapping_type"], r["reference_id"]) for r in b.crosswalk_records] == [
        (25, "mapped", "ID.SC-2"), (26, "new_in_2_0", None)]
    assert len(b.conflicts) == 1 and b.conflicts[0]["kind"] == "mapped_and_new_in_2_0"
    assert b.conflicts[0]["citations"] == ["xwalk:row25", "xwalk:row26"]
    assert b.unmapped_controls == []  # it does have a mapping, so it is not simply 'unmapped'


def test_1_1_element_with_no_crosswalk_row_is_reported_as_absence_only(assembler, store):
    target = store.controls_without_later_mapping("subcategory")[0]["original_id"]
    b = assembler.assemble(f"How does {target} map to CSF 2.0?")
    assert b.crosswalk_records == []
    assert b.unmapped_controls and b.unmapped_controls[0]["reason"] == NO_REF_REASON
    assert "removed" in NO_REF_REASON and [r["version"] for r in b.control_records] == ["1.1"]


def test_cross_version_comparison_gathers_both_versions_and_official_links(assembler):
    b = assembler.assemble("What are the differences between CSF 1.1 and 2.0 for supply chain "
                           "risk management?")
    assert b.query_type == "cross_version_comparison" and b.searched_versions == ["1.1", "2.0"]
    assert {p["version"] for p in b.passages} == {"1.1", "2.0"}
    assert b.crosswalk_records and all(r["via"][0].startswith(("retrieved:", "category_expansion:")) for r in b.crosswalk_records)
    assert 22 in {r["excel_row"] for r in b.crosswalk_records}      # the category-level official row (see test_category_expansion)
    assert len(b.conflicts) <= 1 and b.unresolved_questions == []


def test_new_in_2_0_question_returns_all_official_new_rows(assembler):
    b = assembler.assemble("What is new in CSF 2.0?")
    new_rows = [r for r in b.crosswalk_records if r["mapping_type"] == "new_in_2_0"]
    assert len(new_rows) == 20 and all(r["reference_id"] is None for r in new_rows)
    assert any("baseline" in u for u in b.unresolved_questions)


# ---- ambiguity, unsupported, missing --------------------------------------------------------
def test_ambiguous_version_searches_both_and_says_so(assembler):
    b = assembler.assemble("How should we handle logging?")
    assert b.searched_versions == ["1.1", "2.0"]
    assert any("No framework version" in u for u in b.unresolved_questions)
    assert {p["version"] for p in b.passages} == {"1.1", "2.0"}


def test_unsupported_question_returns_empty_bundle(assembler):
    b = assembler.assemble("   ")
    assert b.query_type == "unsupported" and not (b.passages or b.control_records
                                                  or b.crosswalk_records or b.citations)
    assert b.unresolved_questions


def test_unknown_control_is_missing_evidence_and_mapping_not_invented(assembler):
    b = assembler.assemble("How does GV.XX-99 map to CSF 1.1?")
    assert b.control_records == [] and b.crosswalk_records == []
    assert b.missing_evidence[0] == {"kind": "control_not_found", "control_id": "GV.XX-99",
                                     "versions_checked": ["1.1", "2.0"]}


def test_no_passages_is_reported(store):
    b = EvidenceAssembler(store, lambda q, k, v: [], "empty").assemble(
        "What does CSF 2.0 say about zzzzqqq?")
    assert b.passages == []
    assert b.missing_evidence == [{"kind": "no_passages", "version": "2.0",
                                   "detail": "retrieval returned nothing for this version"}]


def test_structured_only_mode_without_retriever(store):
    b = EvidenceAssembler(store).assemble("How does GV.OC-01 map to CSF 1.1?")
    assert b.retrieval["mode"] == "none" and b.passages == [] and len(b.crosswalk_records) == 2


def test_assembly_is_deterministic(assembler):
    q = "Compare GV.SC-03 between versions"
    assert assembler.assemble(q).to_dict() == assembler.assemble(q).to_dict()


# ---- citation provenance and validation -------------------------------------------------------
QUESTIONS = ["What does GV.SC-03 require?", "How does GV.OC-01 map to CSF 1.1?",
             "How does GV.SC-03 map to CSF 1.1?", "What is new in CSF 2.0?",
             "What does CSF 1.1 say about data at rest?", "How should we handle logging?",
             "Which CSF 2.0 controls correspond to ID.SC-1?"]


@pytest.mark.parametrize("question", QUESTIONS)
def test_every_citation_in_a_bundle_is_structurally_valid(assembler, store, question):
    b = assembler.assemble(question)
    report = validate_bundle(store, b)
    assert report["invalid"] == 0 and report["citations_checked"] == len(b.citations)
    assert "semantic" in report["scope"]
    for entry in b.control_records + b.passages:  # complete provenance on every evidence item
        assert entry["citation_id"] in b.citations
        assert all(entry[f] not in (None, "") for f in
                   ("chunk_id", "version", "source_file", "page", "section", "text"))
    for entry in b.crosswalk_records:
        assert entry["citation_id"] in b.citations and entry["excel_row"] and entry["source_file"]


def test_registry_matches_stored_metadata(assembler, real_db):
    b = assembler.assemble("What does GV.SC-03 require?")
    conn = connect(real_db[0], readonly=True)
    for c in b.citations.values():
        row = conn.execute("SELECT version, source_file, page, section FROM chunk WHERE chunk_id=?",
                           (c["chunk_id"],)).fetchone()
        assert (c["version"], c["source_file"], c["page"], c["section"]) == tuple(row)


@pytest.fixture(scope="module")
def conn(real_db):
    return connect(real_db[0], readonly=True)


def check(conn, claim, allowed=None):
    (res,) = validate_citations(conn, [claim], allowed)
    return res


def test_chunk_citation_validation(conn):
    cid = chunk_citation_id("csf2.0:subcategory:GV.SC-03")
    assert check(conn, CitationClaim(cid)).valid
    assert check(conn, CitationClaim(cid, version="2.0", source_file="nist_csf_2_0.pdf", page=22,
                                     control_id="gv.sc-03")).valid
    bad = check(conn, CitationClaim(cid, version="1.1", page=99, section="Wrong",
                                    source_file="x.pdf", control_id="GV.SC-04"))
    assert not bad.valid and len(bad.errors) == 5 and bad.scope == "structural"
    missing = check(conn, CitationClaim(chunk_citation_id("csf2.0:subcategory:GV.ZZ-99")))
    assert not missing.valid and "does not exist" in missing.errors[0]
    narrative = check(conn, CitationClaim(chunk_citation_id(
        conn.execute("SELECT chunk_id FROM chunk WHERE chunk_type='text' LIMIT 1").fetchone()[0]),
        control_id="GV.SC-03"))
    assert not narrative.valid


def test_crosswalk_citation_validation(conn):
    cid = xwalk_citation_id(4)
    assert check(conn, CitationClaim(cid, focal_id="GV.OC-01", reference_id="ID.BE-2")).valid
    assert not check(conn, CitationClaim(cid, focal_id="GV.OC-02")).valid
    assert not check(conn, CitationClaim(cid, reference_id="ID.BE-3")).valid
    new_row = xwalk_citation_id(26)
    assert check(conn, CitationClaim(new_row, focal_id="GV.SC-03", check_reference=True)).valid
    assert not check(conn, CitationClaim(new_row, reference_id="ID.SC-2")).valid  # invented mapping
    assert not check(conn, CitationClaim(xwalk_citation_id(999))).valid
    assert not check(conn, CitationClaim("xwalk:rowABC")).valid
    assert not check(conn, CitationClaim(cid, version="3.0")).valid


def test_unrecognised_and_out_of_bundle_citations(conn):
    assert not check(conn, CitationClaim("made-up")).valid
    cid = chunk_citation_id("csf2.0:subcategory:GV.SC-03")
    res = check(conn, CitationClaim(cid), allowed={"chunk:other"})
    assert not res.valid and "not part of the supplied evidence bundle" in res.errors[0]


def test_tampered_bundle_is_detected(assembler, store):
    b = assembler.assemble("What does GV.SC-03 require?")
    b.control_records[0]["text"] += " (edited)"
    b.citations[b.control_records[0]["citation_id"]]["page"] = 3
    report = validate_bundle(store, b)
    assert report["invalid"] == 1
    assert any("page mismatch" in e for e in next(iter(report["errors"].values())))


# ---- CLI ------------------------------------------------------------------------------------------------
def test_cli_prints_bundle_json(real_db, tmp_path, capsys):
    build_bm25(load_corpus(real_db[0]), tmp_path)
    base = ["--db", str(real_db[0]), "--index-dir", str(tmp_path), "--retrieval", "bm25"]
    assert main(["How does GV.SC-03 map to CSF 1.1?", *base, "--compact"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["query_type"] == "control_mapping" and out["conflicts"]
    assert out["citation_validation"]["invalid"] == 0
    assert main(["What does GV.SC-03 require?", "--db", str(real_db[0]), "--retrieval", "none"]) == 0
    assert json.loads(capsys.readouterr().out)["passages"] == []


def test_cli_errors(real_db, tmp_path, capsys):
    assert main(["q", "--db", str(tmp_path / "none.db"), "--retrieval", "none"]) == 2
    assert main(["q", "--db", str(real_db[0]), "--index-dir", str(tmp_path / "no"),
                 "--retrieval", "bm25"]) == 2
    assert "error:" in capsys.readouterr().err


def test_incidental_new_does_not_pull_in_comparison_evidence(assembler):
    b = assembler.assemble("What new technologies like AI does CSF 2.0 address?")
    assert b.query_type == "single_version" and b.searched_versions == ["2.0"]
    assert b.crosswalk_records == [] and {p["version"] for p in b.passages} == {"2.0"}


def test_unanchored_change_question_is_flagged_ambiguous_in_the_bundle(assembler):
    b = assembler.assemble("What changed?")
    assert b.query_type == "single_version" and b.crosswalk_records == []
    assert any("no comparison was assumed" in u for u in b.unresolved_questions)
    assert b.searched_versions == ["1.1", "2.0"]
