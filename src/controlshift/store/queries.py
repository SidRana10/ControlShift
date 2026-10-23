"""Deterministic read-only queries over the SQLite store (no PDF parsing, no LLM)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Self

from ..ingest.models import normalize_control_id
from .schema import FOCAL_VERSION, REFERENCE_VERSION, connect


class NotFoundError(LookupError):
    """The requested control does not exist in the given framework version."""


def _rows(cur: sqlite3.Cursor) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


class KnowledgeStore:
    def __init__(self, db_path: str | Path):
        if not Path(db_path).is_file():
            raise FileNotFoundError(f"database not found: {db_path} - run `controlshift-db build`")
        self.conn = connect(db_path, readonly=True)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- helpers -----------------------------------------------------------------------
    def _check_version(self, version: str) -> None:
        if not self.conn.execute("SELECT 1 FROM framework_version WHERE version=?",
                                 (version,)).fetchone():
            raise NotFoundError(f"unknown framework version {version!r}")

    def _require(self, element_id: str, version: str) -> str:
        """Normalise an ID (PR.AT-1 or PR.AT-01) and ensure it exists in `version`."""
        self._check_version(version)
        eid = normalize_control_id(element_id)
        if not self.conn.execute("SELECT 1 FROM element WHERE version=? AND element_id=?",
                                 (version, eid)).fetchone():
            raise NotFoundError(f"{element_id} not found in CSF {version}")
        return eid

    # -- queries -----------------------------------------------------------------------
    def get_control(self, element_id: str, version: str) -> dict | None:
        """The control (function/category/subcategory) in one version, or None if absent."""
        row = self.conn.execute(
            "SELECT * FROM element WHERE version=? AND element_id=?",
            (version, normalize_control_id(element_id))).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["informative_references"] = [r[0] for r in self.conn.execute(
            "SELECT reference_text FROM informative_reference WHERE version=? AND element_id=?"
            " ORDER BY ordinal", (version, out["element_id"]))]
        return out

    def list_controls_in_category(self, category_id: str, version: str) -> list[dict]:
        """Subcategories of a category. Raises NotFoundError for an unknown category."""
        cid = self._require(category_id, version)
        return _rows(self.conn.execute(
            "SELECT * FROM element WHERE version=? AND category_id=? AND level='subcategory'"
            " ORDER BY element_id", (version, cid)))

    def mappings_2_0_to_1_1(self, element_id: str) -> list[dict]:
        """Official crosswalk rows for a CSF 2.0 element, in workbook order.

        A conceptually new element yields its single official row with reference_* = None.
        """
        eid = self._require(element_id, FOCAL_VERSION)
        return _rows(self.conn.execute(
            "SELECT * FROM crosswalk_mapping WHERE focal_element_id=? ORDER BY excel_row", (eid,)))

    def mappings_1_1_to_2_0(self, element_id: str) -> list[dict]:
        """Official rows that reference a CSF 1.1 element (reverse lookup; may be empty)."""
        eid = self._require(element_id, REFERENCE_VERSION)
        return _rows(self.conn.execute(
            "SELECT * FROM crosswalk_mapping WHERE reference_element_id=? ORDER BY excel_row",
            (eid,)))

    def get_evidence(self, element_id: str, version: str) -> list[dict]:
        """Chunks that support a control: its own chunk first, then narrative chunks that
        mention its ID, in document order. Every chunk carries page/section provenance."""
        eid = self._require(element_id, version)
        return _rows(self.conn.execute(
            """SELECT c.chunk_id, c.version, c.source_file, c.chunk_type, c.page, c.printed_page,
                      c.section, c.text, 'control' AS relation
                 FROM chunk c WHERE c.version=? AND c.element_id=?
               UNION ALL
               SELECT c.chunk_id, c.version, c.source_file, c.chunk_type, c.page, c.printed_page,
                      c.section, c.text, 'mention' AS relation
                 FROM chunk_mention m JOIN chunk c ON c.chunk_id = m.chunk_id
                WHERE m.version=? AND m.element_id=?
               ORDER BY relation, page, chunk_id""", (version, eid, version, eid)))

    def controls_without_earlier_mapping(self, level: str | None = None) -> list[dict]:
        """CSF 2.0 elements with no official 1.1 counterpart (the 'conceptually new' ones)."""
        sql = ("SELECT e.* FROM element e WHERE e.version=? AND NOT EXISTS ("
               " SELECT 1 FROM crosswalk_mapping m WHERE m.focal_element_id=e.element_id"
               " AND m.reference_element_id IS NOT NULL)")
        args: list[str] = [FOCAL_VERSION]
        if level:
            sql += " AND e.level=?"
            args.append(level)
        return _rows(self.conn.execute(sql + " ORDER BY e.element_id", args))

    def controls_without_later_mapping(self, level: str | None = None) -> list[dict]:
        """CSF 1.1 elements that no crosswalk row points to."""
        sql = ("SELECT e.* FROM element e WHERE e.version=? AND NOT EXISTS ("
               " SELECT 1 FROM crosswalk_mapping m WHERE m.reference_element_id=e.element_id)")
        args: list[str] = [REFERENCE_VERSION]
        if level:
            sql += " AND e.level=?"
            args.append(level)
        return _rows(self.conn.execute(sql + " ORDER BY e.element_id", args))

    def controls_flagged_new_in_2_0(self) -> list[dict]:
        """CSF 2.0 elements the workbook marks 'Conceptually new in 2.0' on at least one row.

        Wider than controls_without_earlier_mapping: an element can carry both a mapped row
        and a 'new' row in the official workbook (e.g. GV.SC-03).
        """
        return _rows(self.conn.execute(
            "SELECT e.* FROM element e WHERE e.version=? AND EXISTS ("
            " SELECT 1 FROM crosswalk_mapping m WHERE m.focal_element_id=e.element_id"
            " AND m.mapping_type='new_in_2_0') ORDER BY e.element_id", (FOCAL_VERSION,)))

    # -- catalog (browse/search) --------------------------------------------------------
    def list_versions(self) -> list[dict]:
        """Framework versions with their source PDF and per-level element counts."""
        out = []
        for v in _rows(self.conn.execute(
                "SELECT f.version, f.name, f.source_file, d.kind, d.sha256, d.bytes, d.pages"
                " FROM framework_version f JOIN source_document d USING (source_file)"
                " ORDER BY f.version")):
            counts = dict(self.conn.execute(
                "SELECT level, COUNT(*) FROM element WHERE version=? GROUP BY level",
                (v["version"],)).fetchall())
            out.append({**v, "counts": {k: counts.get(k, 0)
                                        for k in ("function", "category", "subcategory")}})
        return out

    def list_elements(self, *, version: str | None = None, level: str | None = None,
                      function_id: str | None = None, category_id: str | None = None,
                      q: str | None = None) -> list[dict]:
        """Elements ordered by (version, element_id). `q` is a case-insensitive substring match
        over element_id, original_id, name and description (LIKE wildcards are escaped)."""
        where, args = [], []
        for col, val in (("version", version), ("level", level), ("function_id", function_id),
                         ("category_id", category_id)):
            if val is not None:
                where.append(f"{col}=?")
                args.append(val)
        if q:
            pat = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            where.append("(" + " OR ".join(
                f"COALESCE({c}, '') LIKE ? ESCAPE '\\'"
                for c in ("element_id", "original_id", "name", "description")) + ")")
            args += [pat] * 4
        sql = "SELECT * FROM element" + (" WHERE " + " AND ".join(where) if where else "")
        return _rows(self.conn.execute(sql + " ORDER BY version, element_id", args))

    def list_crosswalk(self, *, focal: str | None = None, reference: str | None = None,
                       mapping_type: str | None = None, q: str | None = None,
                       limit: int = 250, offset: int = 0) -> tuple[int, dict[str, int], list[dict]]:
        """Official workbook rows ordered by excel_row: (total matching, per-type counts ignoring
        `mapping_type`, the requested page). `focal` / `reference` are exact element IDs (either
        spelling). `q` is a case-insensitive substring over both IDs, both descriptions and the
        comment (LIKE wildcards escaped); an all-digit `q` also matches that workbook row."""
        where, args = [], []
        if focal:
            where.append("focal_element_id=?")
            args.append(normalize_control_id(focal.upper()))
        if reference:
            where.append("reference_element_id=?")
            args.append(normalize_control_id(reference.upper()))
        if q:
            pat = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            cols = ("focal_element_id", "focal_original_id", "reference_element_id",
                    "reference_original_id", "focal_description", "reference_description", "comments")
            clause = " OR ".join(f"COALESCE({c}, '') LIKE ? ESCAPE '\\'" for c in cols)
            args_q = [pat] * len(cols)
            if q.isascii() and q.isdigit():
                clause += " OR excel_row=?"
                args_q.append(int(q))
            where.append(f"({clause})")
            args += args_q
        base = " WHERE " + " AND ".join(where) if where else ""
        counts = {t: 0 for t in ("mapped", "new_in_2_0", "unmapped")}
        for t, n in self.conn.execute(
                f"SELECT mapping_type, COUNT(*) FROM crosswalk_mapping{base} GROUP BY 1", args):
            counts[t] = n
        if mapping_type:
            base += (" AND" if where else " WHERE") + " mapping_type=?"
            args = args + [mapping_type]
        total = self.conn.execute(f"SELECT COUNT(*) FROM crosswalk_mapping{base}", args).fetchone()[0]
        rows = _rows(self.conn.execute(
            f"SELECT * FROM crosswalk_mapping{base} ORDER BY excel_row LIMIT ? OFFSET ?",
            args + [limit, offset]))
        return total, counts, rows

    def list_children(self, element_id: str, version: str) -> list[dict]:
        """Direct children (category -> subcategories, function -> categories)."""
        return _rows(self.conn.execute(
            "SELECT * FROM element WHERE version=? AND parent_id=? ORDER BY element_id",
            (version, normalize_control_id(element_id))))

    def get_source_document(self, source_file: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM source_document WHERE source_file=?",
                                (source_file,)).fetchone()
        return dict(row) if row else None
