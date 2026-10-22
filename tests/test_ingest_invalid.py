"""Invalid-input handling and unit tests with synthetic files."""
import shutil

import openpyxl
import pymupdf
import pytest

from controlshift.ingest.cli import main
from controlshift.ingest.crosswalk import parse_crosswalk
from controlshift.ingest.errors import IngestionError
from controlshift.ingest.models import control_level, normalize_control_id, stable_id
from controlshift.ingest.narrative import MAX_CHARS, _pack
from controlshift.ingest.pdf import extract_pages
from controlshift.ingest.pipeline import CROSSWALK_XLSX, CSF11_PDF, CSF20_PDF, run


def make_pdf(path, pages):
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        y = 100
        for line in lines:
            page.insert_text((72, y), line, fontsize=11)
            y += 16
    doc.save(path)


def test_normalize_and_level():
    assert normalize_control_id("PR.AT-1") == "PR.AT-01"
    assert normalize_control_id("PR.AT-01") == "PR.AT-01"
    assert normalize_control_id("GV.OC") == "GV.OC"
    assert [control_level(x) for x in ("GV", "GV.OC", "GV.OC-01")] == [
        "function", "category", "subcategory"]


def test_stable_ids_are_deterministic():
    assert stable_id("2.0", "text", "S", "body") == stable_id("2.0", "text", "S", "body")
    assert stable_id("2.0", "text", "S", "body") != stable_id("2.0", "text", "S", "other")
    assert stable_id("1.1", "subcategory", "PR.AT-1") == "csf1.1:subcategory:PR.AT-1"


def test_pack_respects_max_chars():
    para = ("This is a sentence about controls. " * 100).strip()
    out = _pack([(para, 3, "1"), ("Short tail.", 4, "2")])
    assert all(len(t) <= MAX_CHARS + 20 for t, _, _ in out)
    assert out[0][1] == 3


def test_synthetic_pdf_extraction_strips_header_and_keeps_text(tmp_path):
    pdf = tmp_path / "x.pdf"
    make_pdf(pdf, [["o GV.OC-01: Mission is understood", "and informs risk"]])
    pages = extract_pages(pdf)
    assert [ln.text for ln in pages[0].lines] == [
        "o GV.OC-01: Mission is understood", "and informs risk"]


@pytest.mark.parametrize("content", [b"", b"not a pdf at all"])
def test_garbage_pdf_rejected(tmp_path, content):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(content)
    with pytest.raises(IngestionError):
        extract_pages(bad)


def test_missing_pdf_rejected(tmp_path):
    with pytest.raises(IngestionError, match="not found"):
        extract_pages(tmp_path / "nope.pdf")


def test_pdf_without_text_rejected(tmp_path):
    blank = tmp_path / "blank.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(blank)
    with pytest.raises(IngestionError, match="no extractable text"):
        extract_pages(blank)


def _workbook(path, sheet="Relationships", header=None, rows=()):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header or ["Focal Document\nElement", "Focal Document Element Description",
                         "Reference Document\nElement",
                         "Reference Document\nElement Description\n(Optional)",
                         "Comments\n(Optional)", "Strength of\nRelationship\n(Optional)"])
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_crosswalk_parses_synthetic_rows(tmp_path):
    x = tmp_path / "c.xlsx"
    _workbook(x, rows=[["GV.OC-01", "d", "ID.BE-2", "d1", None, None],
                       ["GV.OV-01", "d", None, None, "Conceptually new in 2.0", None]])
    rows = parse_crosswalk(x)
    assert [r["mapping_type"] for r in rows] == ["mapped", "new_in_2_0"]
    assert [r["excel_row"] for r in rows] == [2, 3]
    assert rows[0]["reference_id_normalized"] == "ID.BE-02"


@pytest.mark.parametrize("kind", ["wrong_sheet", "wrong_columns", "empty", "corrupt", "missing"])
def test_invalid_crosswalk_rejected(tmp_path, kind):
    x = tmp_path / "c.xlsx"
    if kind == "wrong_sheet":
        _workbook(x, sheet="Other", rows=[["a", "b", "c", "d", "e", "f"]])
    elif kind == "wrong_columns":
        _workbook(x, header=["a", "b", "c"], rows=[[1, 2, 3]])
    elif kind == "empty":
        _workbook(x)
    elif kind == "corrupt":
        x.write_bytes(b"PK garbage")
    with pytest.raises(IngestionError):
        parse_crosswalk(x)


def test_pdf_that_is_not_csf_rejected(raw_dir, tmp_path):
    for n in (CSF11_PDF, CSF20_PDF, CROSSWALK_XLSX):
        shutil.copy(raw_dir / n, tmp_path / n)
    make_pdf(tmp_path / CSF20_PDF, [["Just an unrelated document."]])
    with pytest.raises(IngestionError, match="no Core controls"):
        run(tmp_path, tmp_path / "out")


def test_cli_reports_failure_with_exit_code_2(tmp_path, capsys):
    assert main(["--raw-dir", str(tmp_path), "--out-dir", str(tmp_path / "o")]) == 2
    assert "ingestion failed" in capsys.readouterr().err


def test_cli_success(raw_dir, tmp_path, capsys):
    assert main(["--raw-dir", str(raw_dir), "--out-dir", str(tmp_path), "--strict"]) == 0
    assert (tmp_path / "chunks.jsonl").is_file()
