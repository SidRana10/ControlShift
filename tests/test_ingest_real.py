"""Tests against the real NIST documents in data/raw (skipped if absent)."""
import json

from controlshift.ingest.models import normalize_control_id
from controlshift.ingest.pipeline import run


def load(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_core_counts_match_published_structure(ingested):
    _, manifest = ingested
    by = manifest["counts"]["by_version_and_type"]
    assert (by["2.0"]["function"], by["2.0"]["category"], by["2.0"]["subcategory"]) == (6, 22, 106)
    assert (by["1.1"]["function"], by["1.1"]["category"], by["1.1"]["subcategory"]) == (5, 23, 108)
    assert manifest["warnings"] == []


def test_chunk_ids_unique_and_metadata_complete(ingested):
    out, _ = ingested
    chunks = load(out / "chunks.jsonl")
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    for c in chunks:
        assert c["version"] in ("1.1", "2.0")
        assert c["source_file"].endswith(".pdf") and c["page"] >= 1 and c["text"].strip()
        assert c["section"]
        if c["chunk_type"] != "text":
            assert c["control_id"] and c["function_id"]
        else:
            assert len(c["text"]) <= 1700


def test_known_controls(ingested):
    out, _ = ingested
    by_id = {c["chunk_id"]: c for c in load(out / "chunks.jsonl")}
    gv = by_id["csf2.0:subcategory:GV.OC-01"]
    assert gv["text"] == (
        "GV.OC-01: The organizational mission is understood and informs cybersecurity risk management"
    )
    assert gv["category_id"] == "GV.OC" and gv["function_id"] == "GV"
    at = by_id["csf1.1:subcategory:PR.AT-1"]
    assert at["text"] == "PR.AT-1: All users are informed and trained"
    assert "CIS CSC 17, 18" in at["informative_references"]
    assert any(r.startswith("NIST SP 800-53 Rev. 4") for r in at["informative_references"])
    # 1.1 has no Govern function; 2.0 does
    assert "csf1.1:function:GV" not in by_id and "csf2.0:function:GV" in by_id


def test_crosswalk_preserves_rows(ingested):
    out, manifest = ingested
    rows = load(out / "crosswalk.jsonl")
    assert len(rows) == 205 == manifest["counts"]["crosswalk_rows"]
    assert [r["excel_row"] for r in rows] == list(range(2, 207))
    new = [r for r in rows if r["mapping_type"] == "new_in_2_0"]
    assert len(new) == 20 and all(r["reference_id"] is None for r in new)
    first = rows[0]
    assert (first["focal_id"], first["reference_id"]) == ("GV", "ID.GV")
    assert all(r["focal_description"] for r in rows)


def test_crosswalk_ids_resolve_to_pdf_controls(ingested):
    out, _ = ingested
    chunks = load(out / "chunks.jsonl")
    ids = {v: {normalize_control_id(c["control_id"]) for c in chunks
               if c["version"] == v and c["control_id"]} for v in ("1.1", "2.0")}
    for r in load(out / "crosswalk.jsonl"):
        assert r["focal_id_normalized"] in ids["2.0"]
        if r["reference_id"]:
            assert r["reference_id_normalized"] in ids["1.1"]


def test_ingestion_is_byte_reproducible(raw_dir, tmp_path):
    run(raw_dir, tmp_path / "a")
    run(raw_dir, tmp_path / "b")
    for name in ("chunks.jsonl", "crosswalk.jsonl", "manifest.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_references_continued_from_previous_page_are_attached(ingested):
    out, _ = ingested
    by_id = {c["chunk_id"]: c for c in load(out / "chunks.jsonl")}
    ac7 = by_id["csf1.1:subcategory:PR.AC-7"]
    assert "ISA 62443-3-3:2013 SR 1.1, SR 1.2, SR 1.5, SR 1.7, SR 1.8, SR 1.9, SR 1.10" in (
        ac7["informative_references"])
    assert any("AC-11" in r for r in ac7["informative_references"])
    subs = [c for c in by_id.values() if c["version"] == "1.1" and c["chunk_type"] == "subcategory"]
    assert all(len(c["informative_references"]) >= 2 for c in subs)
