"""Build the database from data/processed/*.jsonl + manifest.json (never touches the PDFs)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from ..ingest.models import FUNCTION_NAMES, normalize_control_id
from .schema import DDL, SCHEMA_VERSION, TABLES, connect

VERSION_NAMES = {"1.1": "NIST Cybersecurity Framework 1.1", "2.0": "NIST Cybersecurity Framework 2.0"}
_LEVEL_ORDER = {"function": 0, "category": 1, "subcategory": 2}
_CAT_TEXT = re.compile(r"^(.+?) \(([A-Z]{2}\.[A-Z]{2})\):\s*(.*)$", re.DOTALL)
_SUB_TEXT = re.compile(r"^[A-Z]{2}\.[A-Z]{2}-\d{1,2}:\s*(.*)$", re.DOTALL)
_FN_TEXT = re.compile(r"^[A-Z]+ \([A-Z]{2}\)(?::\s*(.*))?$", re.DOTALL)


class LoadError(Exception):
    """Raised when the processed files are missing/inconsistent; the database is left untouched."""


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise LoadError(f"missing {path} - run `controlshift-ingest` first")
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except json.JSONDecodeError as exc:
        raise LoadError(f"{path.name} is not valid JSONL: {exc}") from exc


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _element_row(c: dict) -> tuple:
    """(version, element_id, original_id, level, name, description, function, category, parent)."""
    level, cid, text = c["chunk_type"], c["control_id"], c["text"]
    if level == "function":
        m = _FN_TEXT.match(text)
        name, desc, parent, cat = FUNCTION_NAMES[cid], (m.group(1) if m else None) or None, None, None
    elif level == "category":
        m = _CAT_TEXT.match(text)
        if not m or m.group(2) != cid:
            raise LoadError(f"cannot parse category chunk {c['chunk_id']}")
        name, desc, parent, cat = m.group(1), m.group(3), cid[:2], cid
    else:
        m = _SUB_TEXT.match(text)
        if not m:
            raise LoadError(f"cannot parse subcategory chunk {c['chunk_id']}")
        name, desc, parent, cat = None, m.group(1), cid[:5], cid[:5]
    return (c["version"], normalize_control_id(cid), cid, level, name, desc, c["function_id"], cat,
            parent)


def build_database(db_path: Path, processed_dir: Path) -> dict[str, int]:
    """Replace the database contents atomically from the processed files.

    All DDL and inserts run in one transaction: on any error nothing changes, and re-running
    with the same inputs yields an identical database (idempotent).
    """
    chunks = _read_jsonl(processed_dir / "chunks.jsonl")
    xwalk = _read_jsonl(processed_dir / "crosswalk.jsonl")
    manifest_path = processed_dir / "manifest.json"
    if not manifest_path.is_file():
        raise LoadError(f"missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        for table in reversed(TABLES):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        for stmt in _statements(DDL):
            conn.execute(stmt)

        for name, meta in manifest["inputs"].items():
            conn.execute("INSERT INTO source_document VALUES (?,?,?,?,?)",
                         (name, "pdf" if name.endswith(".pdf") else "xlsx", meta["sha256"],
                          meta["bytes"], meta.get("pages")))
        files = {c["version"]: c["source_file"] for c in chunks}
        for version in sorted(files):
            conn.execute("INSERT INTO framework_version VALUES (?,?,?)",
                         (version, VERSION_NAMES[version], files[version]))

        controls = sorted((c for c in chunks if c["chunk_type"] != "text"),
                          key=lambda c: (_LEVEL_ORDER[c["chunk_type"]], c["version"], c["control_id"]))
        for c in controls:
            conn.execute("INSERT INTO element VALUES (?,?,?,?,?,?,?,?,?)", _element_row(c))
            for i, ref in enumerate(c.get("informative_references", [])):
                conn.execute("INSERT INTO informative_reference VALUES (?,?,?,?)",
                             (c["version"], normalize_control_id(c["control_id"]), i, ref))

        known = {(r[0], r[1]) for r in conn.execute("SELECT version, element_id FROM element")}
        for i, c in enumerate(chunks):
            eid = normalize_control_id(c["control_id"]) if c["control_id"] else None
            conn.execute("INSERT INTO chunk VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (c["chunk_id"], c["version"], c["source_file"], c["chunk_type"], c["page"],
                          c["printed_page"], c["section"], c["text"], c["char_count"], eid, i))
            for m in sorted({normalize_control_id(x) for x in c.get("mentioned_controls", [])}):
                if (c["version"], m) in known:  # ignore IDs quoted as examples that are not controls
                    conn.execute("INSERT INTO chunk_mention VALUES (?,?,?)",
                                 (c["chunk_id"], c["version"], m))

        for r in sorted(xwalk, key=lambda r: r["excel_row"]):
            conn.execute(
                "INSERT INTO crosswalk_mapping (excel_row, sheet, source_file, focal_element_id,"
                " focal_original_id, focal_description, reference_element_id, reference_original_id,"
                " reference_description, comments, strength, mapping_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["excel_row"], r["sheet"], r["source_file"], r["focal_id_normalized"],
                 r["focal_id"], r["focal_description"], r["reference_id_normalized"],
                 r["reference_id"], r["reference_description"], r["comments"], r["strength"],
                 r["mapping_type"]))

        for k, v in (("schema_version", str(SCHEMA_VERSION)),
                     ("chunks_sha256", _sha(processed_dir / "chunks.jsonl")),
                     ("crosswalk_sha256", _sha(processed_dir / "crosswalk.jsonl")),
                     ("manifest_sha256", _sha(manifest_path))):
            conn.execute("INSERT INTO build_info VALUES (?,?)", (k, v))

        bad = conn.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise LoadError(f"foreign key violations after load: {len(bad)}")
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
        conn.execute("COMMIT")
        return counts
    except BaseException as exc:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        if isinstance(exc, (LoadError, KeyboardInterrupt)):
            raise
        raise LoadError(f"database build failed, no changes made: {exc}") from exc
    finally:
        conn.close()


def _statements(ddl: str) -> list[str]:
    """Split the DDL script on ';' at end of line (no ';' occurs inside our statements)."""
    return [s.strip() for s in re.split(r";\s*\n", ddl) if s.strip()]
