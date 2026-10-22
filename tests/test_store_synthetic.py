"""Phase 2 tests on tiny synthetic processed data: constraints, rollback, bad input."""
import json
import sqlite3

import pytest

from controlshift.ingest.models import normalize_control_id as norm
from controlshift.store.loader import LoadError, build_database
from controlshift.store.schema import connect
from controlshift.store.validate import validate_database


def chunk(version, ctype, cid, text, src, **kw):
    fn = cid[:2] if cid else None
    return {"chunk_id": f"csf{version}:{ctype}:{cid}" if cid else kw.pop("chunk_id"),
            "version": version, "source_file": src, "chunk_type": ctype, "page": 1,
            "printed_page": "1", "section": "S", "text": text, "char_count": len(text),
            "control_id": cid, "function_id": fn,
            "category_id": cid[:5] if cid and len(cid) > 2 else None,
            "informative_references": [], "mentioned_controls": kw.get("mentions", [])}


def write(dirpath, chunks, rows):
    dirpath.mkdir(exist_ok=True)
    (dirpath / "chunks.jsonl").write_text("\n".join(json.dumps(c) for c in chunks) + "\n")
    (dirpath / "crosswalk.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    n = lambda v, t: sum(1 for c in chunks if c["version"] == v and c["chunk_type"] == t)
    manifest = {
        "inputs": {"a.pdf": {"sha256": "x", "bytes": 1, "pages": 1},
                   "b.pdf": {"sha256": "y", "bytes": 1, "pages": 1},
                   "c.xlsx": {"sha256": "z", "bytes": 1}},
        "counts": {"chunks_total": len(chunks), "crosswalk_rows": len(rows),
                   "by_version_and_type": {v: {t: n(v, t) for t in
                                               ("function", "category", "subcategory", "text")
                                               if n(v, t)} for v in ("1.1", "2.0")},
                   "crosswalk_by_mapping_type": {}},
    }
    for r in rows:
        k = manifest["counts"]["crosswalk_by_mapping_type"]
        k[r["mapping_type"]] = k.get(r["mapping_type"], 0) + 1
    (dirpath / "manifest.json").write_text(json.dumps(manifest))


def row(excel_row, focal, ref, mtype="mapped"):
    return {"excel_row": excel_row, "sheet": "Relationships", "source_file": "c.xlsx",
            "focal_id": focal, "focal_id_normalized": norm(focal), "focal_description": "d",
            "reference_id": ref, "reference_id_normalized": norm(ref) if ref else None, "reference_description": None,
            "comments": None, "strength": None, "mapping_type": mtype}


def base_chunks():
    refd = chunk("1.1", "subcategory", "ID.BE-2", "ID.BE-2: place", "b.pdf")
    refd["informative_references"] = ["CIS CSC 1"]
    return [
        chunk("2.0", "function", "GV", "GOVERN (GV): g", "a.pdf"),
        chunk("2.0", "category", "GV.OC", "Org Context (GV.OC): d", "a.pdf"),
        chunk("2.0", "subcategory", "GV.OC-01", "GV.OC-01: mission", "a.pdf"),
        chunk("2.0", "subcategory", "GV.OC-02", "GV.OC-02: new thing", "a.pdf"),
        chunk("1.1", "function", "ID", "IDENTIFY (ID)", "b.pdf"),
        chunk("1.1", "category", "ID.BE", "Business Environment (ID.BE): d", "b.pdf"),
        refd,
        chunk("1.1", "subcategory", "ID.BE-3", "ID.BE-3: priorities", "b.pdf"),
        chunk("2.0", "text", None, "see GV.OC-01 and GV.OC-77", "a.pdf", chunk_id="t1",
              mentions=["GV.OC-01", "GV.OC-77"]),
    ]


def good_rows():
    return [row(2, "GV.OC-01", "ID.BE-2"), row(3, "GV.OC-01", "ID.BE-3"),
            row(4, "GV.OC-02", None, "new_in_2_0"), row(5, "GV", None, "new_in_2_0"),
            row(6, "GV.OC", "ID.BE")]


@pytest.fixture
def processed(tmp_path):
    p = tmp_path / "p"
    write(p, base_chunks(), good_rows())
    return p


def test_builds_and_validates(processed, tmp_path):
    db = tmp_path / "t.db"
    counts = build_database(db, processed)
    assert counts["element"] == 8 and counts["crosswalk_mapping"] == 5
    assert counts["chunk_mention"] == 1  # GV.OC-77 is not a known control and is dropped
    assert validate_database(db, processed) == []


def test_loading_twice_does_not_duplicate(processed, tmp_path):
    db = tmp_path / "t.db"
    first = build_database(db, processed)
    assert build_database(db, processed) == first


def test_failed_rebuild_rolls_back(processed, tmp_path):
    db = tmp_path / "t.db"
    build_database(db, processed)
    bad = tmp_path / "bad"
    write(bad, base_chunks(), good_rows() + [row(9, "GV.OC-01", "NOPE.XX-99")])
    with pytest.raises(LoadError):
        build_database(db, bad)
    conn = connect(db, readonly=True)  # old contents intact
    assert conn.execute("SELECT COUNT(*) FROM crosswalk_mapping").fetchone()[0] == 5


def test_missing_inputs(tmp_path):
    with pytest.raises(LoadError, match="missing"):
        build_database(tmp_path / "x.db", tmp_path / "empty")


def test_malformed_jsonl(processed, tmp_path):
    (processed / "chunks.jsonl").write_text("{not json\n")
    with pytest.raises(LoadError, match="JSONL"):
        build_database(tmp_path / "t.db", processed)


def test_constraints_reject_version_mixing_and_wrong_direction(processed, tmp_path):
    db = tmp_path / "t.db"
    build_database(db, processed)
    conn = connect(db)
    ins = ("INSERT INTO crosswalk_mapping (excel_row, sheet, source_file, focal_version,"
           " focal_element_id, focal_original_id, reference_version, reference_element_id,"
           " mapping_type) VALUES (?,?,?,?,?,?,?,?,?)")
    # reversed direction (1.1 as focal) is rejected
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, (50, "s", "c.xlsx", "1.1", "ID.BE-2", "ID.BE-02", "1.1", "ID.BE-03", "mapped"))
    # a 2.0 ID used as the 1.1 reference does not exist in 1.1 -> FK violation
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, (51, "s", "c.xlsx", "2.0", "GV.OC-01", "GV.OC-01", "1.1", "GV.OC-02", "mapped"))
    # 'mapped' without reference, and 'new' with reference, are both rejected
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, (52, "s", "c.xlsx", "2.0", "GV.OC-01", "GV.OC-01", "1.1", None, "mapped"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, (53, "s", "c.xlsx", "2.0", "GV.OC-02", "GV.OC-02", "1.1", "ID.BE-02",
                           "new_in_2_0"))
    # a chunk cannot cite a source file of the other version
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO chunk VALUES ('z','2.0','b.pdf','text',1,NULL,'S','t',1,NULL,99)")
    # a subcategory cannot reference a parent that is in another version
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO element VALUES ('2.0','GV.OC-09','GV.OC-09','subcategory',NULL,"
                     "'d','GV','ID.BE','ID.BE')")


def test_validate_detects_tampering(processed, tmp_path):
    db = tmp_path / "t.db"
    build_database(db, processed)
    conn = connect(db)
    conn.execute("DELETE FROM crosswalk_mapping WHERE excel_row=2")
    conn.close()
    problems = validate_database(db, processed)
    assert any("crosswalk rows" in p for p in problems)
