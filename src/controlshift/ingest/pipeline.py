"""Orchestrates ingestion and writes reproducible JSONL/JSON outputs."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from .controls import parse_csf11_core, parse_csf20_core
from .crosswalk import parse_crosswalk
from .errors import IngestionError
from .models import Chunk, normalize_control_id
from .narrative import MAX_CHARS, MIN_CHARS, chunk_narrative
from .pdf import extract_pages

CSF11_PDF = "nist_csf_1_1.pdf"
CSF20_PDF = "nist_csf_2_0.pdf"
CROSSWALK_XLSX = "nist_csf_transition.xlsx"

# Published structure of the two Core versions, used only as a sanity check.
EXPECTED = {"1.1": {"function": 5, "category": 23, "subcategory": 108},
            "2.0": {"function": 6, "category": 22, "subcategory": 106}}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def _ingest_version(raw: Path, name: str, version: str) -> tuple[list[Chunk], int]:
    pages = extract_pages(raw / name)
    if version == "1.1":
        core, core_pages = parse_csf11_core(pages, name)
    else:
        core = parse_csf20_core(pages, name)
        core_pages = set(range(min(c.page for c in core), max(c.page for c in core) + 1)) if core else set()
    if not core:
        raise IngestionError(f"{name}: no Core controls found - is this the CSF {version} PDF?")
    text = chunk_narrative(pages, version, name, core_pages)
    return core + text, len(pages)


def run(raw_dir: Path, out_dir: Path) -> dict:
    chunks: list[Chunk] = []
    page_counts: dict[str, int] = {}
    for name, version in ((CSF11_PDF, "1.1"), (CSF20_PDF, "2.0")):
        got, n_pages = _ingest_version(raw_dir, name, version)
        chunks += got
        page_counts[name] = n_pages
    crosswalk = parse_crosswalk(raw_dir / CROSSWALK_XLSX)

    ids = [c.chunk_id for c in chunks]
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    if dupes:
        raise IngestionError(f"duplicate chunk IDs: {dupes[:5]}")

    counts = {v: Counter(c.chunk_type for c in chunks if c.version == v) for v in ("1.1", "2.0")}
    warnings = [
        f"CSF {v}: found {counts[v].get(k, 0)} {k} chunks, expected {n}"
        for v, exp in EXPECTED.items() for k, n in exp.items() if counts[v].get(k, 0) != n
    ]
    # Cross-check: crosswalk IDs must resolve to controls extracted from the PDFs.
    ids11 = {normalize_control_id(c.control_id) for c in chunks if c.version == "1.1" and c.control_id}
    ids20 = {normalize_control_id(c.control_id) for c in chunks if c.version == "2.0" and c.control_id}
    unresolved_focal = sorted({r["focal_id_normalized"] for r in crosswalk} - ids20)
    unresolved_ref = sorted({r["reference_id_normalized"] for r in crosswalk
                             if r["reference_id_normalized"]} - ids11)
    if unresolved_focal:
        warnings.append(f"crosswalk focal IDs not found in CSF 2.0 PDF: {unresolved_focal}")
    if unresolved_ref:
        warnings.append(f"crosswalk reference IDs not found in CSF 1.1 PDF: {unresolved_ref}")

    out_dir.mkdir(parents=True, exist_ok=True)
    chunk_dicts = [c.to_dict() for c in chunks]
    _write_jsonl(out_dir / "chunks.jsonl", chunk_dicts)
    _write_jsonl(out_dir / "crosswalk.jsonl", crosswalk)

    manifest = {
        "inputs": {
            n: {"sha256": _sha256(raw_dir / n), "bytes": (raw_dir / n).stat().st_size,
                **({"pages": page_counts[n]} if n in page_counts else {})}
            for n in (CSF11_PDF, CSF20_PDF, CROSSWALK_XLSX)
        },
        "chunking": {"max_chars": MAX_CHARS, "min_tail_chars": MIN_CHARS},
        "counts": {
            "chunks_total": len(chunks),
            "by_version_and_type": {v: dict(sorted(c.items())) for v, c in counts.items()},
            "crosswalk_rows": len(crosswalk),
            "crosswalk_by_mapping_type": dict(sorted(Counter(r["mapping_type"] for r in crosswalk).items())),
            "crosswalk_by_focal_level": dict(sorted(Counter(r["focal_level"] for r in crosswalk).items())),
        },
        "warnings": warnings,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest
