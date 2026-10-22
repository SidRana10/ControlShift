"""Integrity and manifest-consistency checks for the built database."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .schema import TABLES, connect


def validate_database(db_path: Path, processed_dir: Path) -> list[str]:
    """Return a list of problems (empty = valid)."""
    problems: list[str] = []
    conn = connect(db_path, readonly=True)
    try:
        if (res := conn.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
            problems.append(f"integrity_check: {res}")
        if fk := conn.execute("PRAGMA foreign_key_check").fetchall():
            problems.append(f"{len(fk)} foreign key violations")
        problems += _manifest_checks(conn, processed_dir)
        problems += _semantic_checks(conn)
    except sqlite3.Error as exc:
        problems.append(f"sqlite error: {exc}")
    finally:
        conn.close()
    return problems


def _one(conn: sqlite3.Connection, sql: str, *args) -> int:
    return conn.execute(sql, args).fetchone()[0]


def _manifest_checks(conn: sqlite3.Connection, processed_dir: Path) -> list[str]:
    out: list[str] = []
    path = processed_dir / "manifest.json"
    if not path.is_file():
        return [f"manifest not found at {path}; cannot compare counts"]
    counts = json.loads(path.read_text(encoding="utf-8"))["counts"]
    for version, by_type in counts["by_version_and_type"].items():
        for ctype, n in by_type.items():
            got = _one(conn, "SELECT COUNT(*) FROM chunk WHERE version=? AND chunk_type=?",
                       version, ctype)
            if got != n:
                out.append(f"chunk count {version}/{ctype}: db={got} manifest={n}")
            if ctype != "text":
                got = _one(conn, "SELECT COUNT(*) FROM element WHERE version=? AND level=?",
                           version, ctype)
                if got != n:
                    out.append(f"element count {version}/{ctype}: db={got} manifest={n}")
    if (got := _one(conn, "SELECT COUNT(*) FROM chunk")) != counts["chunks_total"]:
        out.append(f"total chunks: db={got} manifest={counts['chunks_total']}")
    if (got := _one(conn, "SELECT COUNT(*) FROM crosswalk_mapping")) != counts["crosswalk_rows"]:
        out.append(f"crosswalk rows: db={got} manifest={counts['crosswalk_rows']}")
    for mtype, n in counts["crosswalk_by_mapping_type"].items():
        got = _one(conn, "SELECT COUNT(*) FROM crosswalk_mapping WHERE mapping_type=?", mtype)
        if got != n:
            out.append(f"crosswalk {mtype}: db={got} manifest={n}")
    return out


def _semantic_checks(conn: sqlite3.Connection) -> list[str]:
    out: list[str] = []
    for table in TABLES:
        if _one(conn, f"SELECT COUNT(*) FROM {table}") == 0:
            out.append(f"table {table} is empty")
    if n := _one(conn, "SELECT COUNT(*) FROM element e WHERE e.version='2.0' AND NOT EXISTS ("
                       "SELECT 1 FROM crosswalk_mapping m WHERE m.focal_element_id=e.element_id)"):
        out.append(f"{n} CSF 2.0 elements have no crosswalk row")
    if n := _one(conn, "SELECT COUNT(*) FROM crosswalk_mapping WHERE mapping_type='new_in_2_0'"
                       " AND reference_element_id IS NOT NULL"):
        out.append(f"{n} 'new_in_2_0' rows carry a reference (invented mapping?)")
    if n := _one(conn, "SELECT COUNT(*) FROM element s JOIN element p ON p.version=s.version"
                       " AND p.element_id=s.parent_id WHERE s.level='subcategory'"
                       " AND p.category_id IS NOT s.category_id"):
        out.append(f"{n} subcategories whose parent category differs from category_id")
    return out
