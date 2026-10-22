"""Phase 2 tests against the real NIST data."""
import json
import sqlite3

import pytest

from controlshift.store.cli import main
from controlshift.store.loader import build_database
from controlshift.store.queries import KnowledgeStore, NotFoundError
from controlshift.store.schema import connect
from controlshift.store.validate import validate_database


@pytest.fixture(scope="module")
def store(real_db):
    with KnowledgeStore(real_db[0]) as s:
        yield s


def test_counts_match_phase1_manifest(real_db):
    db, processed, counts = real_db
    manifest = json.loads((processed / "manifest.json").read_text())["counts"]
    assert counts["chunk"] == manifest["chunks_total"] == 384
    assert counts["crosswalk_mapping"] == manifest["crosswalk_rows"] == 205
    assert counts["element"] == 270  # (6+22+106) + (5+23+108)
    assert validate_database(db, processed) == []


def test_integrity_and_foreign_keys(real_db):
    conn = connect(real_db[0], readonly=True)
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_get_control_both_id_spellings_and_versions(store):
    c = store.get_control("PR.AT-1", "1.1")
    assert c["original_id"] == "PR.AT-1" and c["element_id"] == "PR.AT-01"
    assert c["description"] == "All users are informed and trained"
    assert "CIS CSC 17, 18" in c["informative_references"]
    assert store.get_control("PR.AT-01", "1.1")["element_id"] == "PR.AT-01"
    g = store.get_control("GV.OC-01", "2.0")
    assert g["category_id"] == "GV.OC" and g["parent_id"] == "GV.OC"
    # versions never mix: GV exists only in 2.0, PR.AT-01 is not in 2.0
    assert store.get_control("GV", "1.1") is None
    assert store.get_control("GV", "2.0")["name"] == "Govern"
    assert store.get_control("PR.AC-1", "1.1") is not None
    assert store.get_control("PR.AC-01", "2.0") is None  # PR.AC exists only in 1.1


def test_missing_controls(store):
    assert store.get_control("ZZ.ZZ-99", "2.0") is None
    with pytest.raises(NotFoundError):
        store.list_controls_in_category("ZZ.ZZ", "2.0")
    with pytest.raises(NotFoundError):
        store.mappings_2_0_to_1_1("ZZ.ZZ-99")
    with pytest.raises(NotFoundError):
        store.mappings_1_1_to_2_0("GV.OC-01")  # a 2.0-only ID asked of 1.1
    with pytest.raises(NotFoundError):
        store.get_evidence("GV.OC-01", "9.9")


def test_list_controls_in_category(store):
    subs = store.list_controls_in_category("GV.OC", "2.0")
    assert [s["element_id"] for s in subs] == [f"GV.OC-0{i}" for i in range(1, 6)]
    assert all(s["version"] == "2.0" and s["level"] == "subcategory" for s in subs)
    assert len(store.list_controls_in_category("PR.AC", "1.1")) == 7


def test_one_to_many_forward_mapping_preserves_rows(store):
    rows = store.mappings_2_0_to_1_1("GV.OC-01")
    assert [(r["excel_row"], r["reference_original_id"]) for r in rows] == [(4, "ID.BE-2"),
                                                                           (5, "ID.BE-3")]
    assert all(r["focal_version"] == "2.0" and r["reference_version"] == "1.1" for r in rows)
    assert rows[0]["focal_original_id"] == "GV.OC-01" and rows[0]["source_file"].endswith(".xlsx")


def test_reverse_mapping_is_derived_from_stored_rows(store):
    rows = store.mappings_1_1_to_2_0("ID.BE-2")
    assert "GV.OC-01" in {r["focal_original_id"] for r in rows}
    for r in rows:  # every reverse hit is exactly an official forward row
        assert r in store.mappings_2_0_to_1_1(r["focal_element_id"])


def test_new_in_2_0_entries_are_not_invented(store):
    flagged = store.controls_flagged_new_in_2_0()
    assert len(flagged) == 20
    row = store.mappings_2_0_to_1_1("GV.OV-01")
    assert len(row) == 1 and row[0]["mapping_type"] == "new_in_2_0"
    assert row[0]["reference_element_id"] is None and row[0]["reference_original_id"] is None
    unmapped = {c["element_id"] for c in store.controls_without_earlier_mapping()}
    assert "GV.OV-01" in unmapped and "GV.OC-01" not in unmapped
    # Official-data quirk: GV.SC-03 has a mapped row AND a 'new' row, so it is flagged
    # new but still has an earlier mapping.
    assert "GV.SC-03" not in unmapped and "GV.SC-03" in {c["element_id"] for c in flagged}
    assert len(unmapped) == 19


def test_controls_without_later_mapping_only_1_1(store):
    rows = store.controls_without_later_mapping("subcategory")
    assert rows and all(r["version"] == "1.1" for r in rows)


def test_evidence_has_provenance(store):
    ev = store.get_evidence("PR.AT-1", "1.1")
    assert ev[0]["relation"] == "control" and ev[0]["chunk_id"] == "csf1.1:subcategory:PR.AT-1"
    assert ev[0]["page"] >= 1 and ev[0]["source_file"] == "nist_csf_1_1.pdf" and ev[0]["section"]
    assert all(e["version"] == "1.1" for e in ev)


def test_rebuild_is_idempotent(real_db, tmp_path):
    db, processed, counts = real_db
    again = tmp_path / "again.db"
    assert build_database(again, processed) == counts
    assert build_database(again, processed) == counts  # second load into same file

    def dump(p):
        return "\n".join(sqlite3.connect(p).iterdump())

    assert dump(db) == dump(again)


def test_cli_build_validate_and_queries(real_db, tmp_path, capsys):
    _, processed, _ = real_db
    db = tmp_path / "cli.db"
    base = ["--db", str(db), "--processed-dir", str(processed)]
    assert main([*base, "build"]) == 0
    assert main([*base, "validate"]) == 0
    assert main([*base, "inspect"]) == 0
    capsys.readouterr()
    assert main([*base, "map", "GV.OC-01", "--version", "2.0"]) == 0
    assert "ID.BE-2" in capsys.readouterr().out
    assert main([*base, "get", "NOPE.XX-01", "--version", "2.0"]) == 2
    assert main([*base, "unmapped", "--direction", "flagged-new"]) == 0
