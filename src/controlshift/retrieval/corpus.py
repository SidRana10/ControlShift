"""Build the searchable corpus from the SQLite knowledge store (never from the PDFs)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from ..store.schema import connect


class CorpusError(Exception):
    """The database is missing or empty."""


@dataclass(frozen=True)
class Doc:
    chunk_id: str
    version: str
    chunk_type: str
    control_id: str | None  # as printed in the source (PR.AT-1)
    element_id: str | None  # zero-padded (PR.AT-01)
    source_file: str
    page: int
    printed_page: str | None
    section: str
    text: str  # original chunk text (what gets shown/cited)
    index_text: str  # text actually embedded / tokenised (adds control title + context)

    def meta(self) -> dict:
        d = asdict(self)
        d.pop("index_text")
        return d


_SQL = """
SELECT c.chunk_id, c.version, c.chunk_type, c.source_file, c.page, c.printed_page, c.section,
       c.text, e.original_id, e.element_id, e.level, e.name, e.description,
       cat.name AS category_name, fn.name AS function_name
  FROM chunk c
  LEFT JOIN element e   ON e.version = c.version AND e.element_id = c.element_id
  LEFT JOIN element cat ON cat.version = e.version AND cat.element_id = e.category_id
  LEFT JOIN element fn  ON fn.version = e.version AND fn.element_id = e.function_id
 ORDER BY c.ordinal
"""


def _index_text(r: sqlite3.Row) -> str:
    """Context-enriched text: control chunks get ID, level, function and category titles."""
    if r["chunk_type"] == "text":
        return f"{r['section']}: {r['text']}"
    cid, level = r["original_id"], r["level"]
    if level == "function":
        head = f"{cid} {r['name']} function"
        return f"{head}: {r['description']}" if r["description"] else head
    if level == "category":
        return (f"{cid} {r['name']} category ({r['function_name']}): {r['description']}")
    return (f"{cid} subcategory ({r['function_name']} / {r['category_name']}): "
            f"{r['description']}")


def load_corpus(db_path: str | Path) -> list[Doc]:
    if not Path(db_path).is_file():
        raise CorpusError(f"database not found: {db_path} - run `controlshift-db build`")
    conn = connect(db_path, readonly=True)
    try:
        rows = conn.execute(_SQL).fetchall()
    finally:
        conn.close()
    if not rows:
        raise CorpusError("database contains no chunks")
    return [
        Doc(chunk_id=r["chunk_id"], version=r["version"], chunk_type=r["chunk_type"],
            control_id=r["original_id"], element_id=r["element_id"],
            source_file=r["source_file"], page=r["page"], printed_page=r["printed_page"],
            section=r["section"], text=r["text"], index_text=_index_text(r))
        for r in rows
    ]


def content_hash(docs: list[Doc]) -> str:
    """Hash of everything that influences indexing (IDs, versions and indexed text)."""
    h = hashlib.sha256()
    for d in docs:
        h.update(json.dumps([d.chunk_id, d.version, d.index_text], ensure_ascii=False).encode())
    return h.hexdigest()
