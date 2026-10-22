"""SQLite schema. Composite (version, id) keys keep CSF 1.1 and 2.0 from being mixed."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1
FOCAL_VERSION = "2.0"  # the official workbook maps CSF 2.0 (focal) -> CSF 1.1 (reference)
REFERENCE_VERSION = "1.1"

TABLES = (
    "source_document", "framework_version", "element", "informative_reference",
    "chunk", "chunk_mention", "crosswalk_mapping", "build_info",
)

DDL = f"""
CREATE TABLE source_document (
    source_file TEXT PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('pdf', 'xlsx')),
    sha256      TEXT NOT NULL,
    bytes       INTEGER NOT NULL,
    pages       INTEGER
);

CREATE TABLE framework_version (
    version     TEXT PRIMARY KEY CHECK (version IN ('1.1', '2.0')),
    name        TEXT NOT NULL,
    source_file TEXT NOT NULL REFERENCES source_document(source_file),
    UNIQUE (version, source_file)
);

-- Functions, categories and subcategories. element_id is the zero-padded form
-- (PR.AT-01); original_id is the spelling printed in the source (PR.AT-1).
CREATE TABLE element (
    version     TEXT NOT NULL REFERENCES framework_version(version),
    element_id  TEXT NOT NULL,
    original_id TEXT NOT NULL,
    level       TEXT NOT NULL CHECK (level IN ('function', 'category', 'subcategory')),
    name        TEXT,
    description TEXT,
    function_id TEXT NOT NULL,
    category_id TEXT,
    parent_id   TEXT,
    PRIMARY KEY (version, element_id),
    UNIQUE (version, original_id),
    FOREIGN KEY (version, parent_id) REFERENCES element(version, element_id),
    CHECK ((level = 'function') = (parent_id IS NULL)),
    CHECK ((level = 'function') = (category_id IS NULL))
);
CREATE INDEX idx_element_level    ON element(version, level);
CREATE INDEX idx_element_category ON element(version, category_id);
CREATE INDEX idx_element_function ON element(version, function_id);

CREATE TABLE informative_reference (
    version        TEXT NOT NULL,
    element_id     TEXT NOT NULL,
    ordinal        INTEGER NOT NULL,
    reference_text TEXT NOT NULL,
    PRIMARY KEY (version, element_id, ordinal),
    FOREIGN KEY (version, element_id) REFERENCES element(version, element_id)
);

CREATE TABLE chunk (
    chunk_id     TEXT PRIMARY KEY,
    version      TEXT NOT NULL,
    source_file  TEXT NOT NULL,
    chunk_type   TEXT NOT NULL CHECK (chunk_type IN ('function','category','subcategory','text')),
    page         INTEGER NOT NULL CHECK (page >= 1),
    printed_page TEXT,
    section      TEXT NOT NULL,
    text         TEXT NOT NULL,
    char_count   INTEGER NOT NULL,
    element_id   TEXT,
    ordinal      INTEGER NOT NULL,
    UNIQUE (chunk_id, version),
    FOREIGN KEY (version, source_file) REFERENCES framework_version(version, source_file),
    FOREIGN KEY (version, element_id)  REFERENCES element(version, element_id),
    CHECK ((chunk_type = 'text') = (element_id IS NULL))
);
CREATE INDEX idx_chunk_element ON chunk(version, element_id);
CREATE INDEX idx_chunk_type    ON chunk(version, chunk_type);
CREATE INDEX idx_chunk_page    ON chunk(version, page);

-- Narrative chunks that mention a control ID (exact-match extraction done in Phase 1).
CREATE TABLE chunk_mention (
    chunk_id   TEXT NOT NULL,
    version    TEXT NOT NULL,
    element_id TEXT NOT NULL,
    PRIMARY KEY (chunk_id, element_id),
    FOREIGN KEY (chunk_id, version)    REFERENCES chunk(chunk_id, version),
    FOREIGN KEY (version, element_id)  REFERENCES element(version, element_id)
);
CREATE INDEX idx_mention_element ON chunk_mention(version, element_id);

-- One row per original workbook row. Direction is fixed: CSF 2.0 (focal) -> CSF 1.1 (reference).
-- Rows for elements that are conceptually new in 2.0 have no reference element.
CREATE TABLE crosswalk_mapping (
    excel_row            INTEGER PRIMARY KEY,
    sheet                TEXT NOT NULL,
    source_file          TEXT NOT NULL REFERENCES source_document(source_file),
    focal_version        TEXT NOT NULL DEFAULT '{FOCAL_VERSION}' CHECK (focal_version = '{FOCAL_VERSION}'),
    focal_element_id     TEXT NOT NULL,
    focal_original_id    TEXT NOT NULL,
    focal_description    TEXT,
    reference_version    TEXT NOT NULL DEFAULT '{REFERENCE_VERSION}'
                         CHECK (reference_version = '{REFERENCE_VERSION}'),
    reference_element_id TEXT,
    reference_original_id TEXT,
    reference_description TEXT,
    comments             TEXT,
    strength             TEXT,
    mapping_type         TEXT NOT NULL CHECK (mapping_type IN ('mapped', 'new_in_2_0', 'unmapped')),
    FOREIGN KEY (focal_version, focal_element_id) REFERENCES element(version, element_id),
    FOREIGN KEY (reference_version, reference_element_id) REFERENCES element(version, element_id),
    CHECK ((mapping_type = 'mapped') = (reference_element_id IS NOT NULL))
);
CREATE INDEX idx_xwalk_focal     ON crosswalk_mapping(focal_element_id);
CREATE INDEX idx_xwalk_reference ON crosswalk_mapping(reference_element_id);
CREATE INDEX idx_xwalk_type      ON crosswalk_mapping(mapping_type);

CREATE TABLE build_info (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: str | Path, *, readonly: bool = False) -> sqlite3.Connection:
    """Open a connection with foreign keys on and manual transaction control."""
    if readonly:
        conn = sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True,
                               isolation_level=None)
    else:
        conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
