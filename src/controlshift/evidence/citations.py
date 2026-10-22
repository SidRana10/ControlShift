"""Structural citation validation.

Checks that citations point at things that exist and that the stated provenance (version, page,
section, source file, mapping endpoints) equals what the database stores. It does NOT check
whether a claim made in an answer is supported by the cited text - that is semantic
faithfulness, evaluated separately.
"""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field

from ..ingest.models import normalize_control_id as _normalize


def normalize_control_id(raw: str) -> str:
    return _normalize(raw.strip().upper())


CHUNK_PREFIX = "chunk:"
XWALK_PREFIX = "xwalk:row"


def chunk_citation_id(chunk_id: str) -> str:
    return f"{CHUNK_PREFIX}{chunk_id}"


def xwalk_citation_id(excel_row: int) -> str:
    return f"{XWALK_PREFIX}{excel_row}"


@dataclass
class CitationClaim:
    """What a citing party (e.g. a future answer generator) asserts about a citation.
    Only the fields that are set are compared with the database."""

    citation_id: str
    version: str | None = None  # chunk: framework version of the chunk
    source_file: str | None = None
    page: int | None = None
    section: str | None = None
    control_id: str | None = None  # chunk: control the chunk is about (any ID spelling)
    focal_id: str | None = None  # crosswalk: CSF 2.0 element
    reference_id: str | None = None  # crosswalk: CSF 1.1 element (None = no reference asserted)
    check_reference: bool = False  # set True to assert that reference_id (even None) is exact


@dataclass
class CitationCheck:
    citation_id: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    scope: str = "structural"  # never 'semantic'

    def to_dict(self) -> dict:
        return asdict(self)


def _check_chunk(conn: sqlite3.Connection, claim: CitationClaim, chunk_id: str) -> list[str]:
    row = conn.execute(
        "SELECT c.version, c.source_file, c.page, c.section, e.element_id, e.original_id "
        "FROM chunk c LEFT JOIN element e ON e.version=c.version AND e.element_id=c.element_id "
        "WHERE c.chunk_id=?", (chunk_id,)).fetchone()
    if row is None:
        return [f"chunk {chunk_id!r} does not exist"]
    errors = []
    for name, stored in (("version", row["version"]), ("source_file", row["source_file"]),
                         ("page", row["page"]), ("section", row["section"])):
        claimed = getattr(claim, name)
        if claimed is not None and claimed != stored:
            errors.append(f"{name} mismatch: cited {claimed!r}, stored {stored!r}")
    if claim.control_id is not None:
        if row["element_id"] is None:
            errors.append(f"chunk is narrative text, not control {claim.control_id!r}")
        elif normalize_control_id(claim.control_id) != row["element_id"]:
            errors.append(f"control mismatch: cited {claim.control_id!r}, stored "
                          f"{row['original_id']!r}")
    return errors


def _check_xwalk(conn: sqlite3.Connection, claim: CitationClaim, excel_row: int) -> list[str]:
    row = conn.execute("SELECT * FROM crosswalk_mapping WHERE excel_row=?",
                       (excel_row,)).fetchone()
    if row is None:
        return [f"crosswalk row {excel_row} does not exist"]
    errors = []
    if claim.focal_id is not None and normalize_control_id(claim.focal_id) != row["focal_element_id"]:
        errors.append(f"focal element mismatch: cited {claim.focal_id!r}, stored "
                      f"{row['focal_original_id']!r}")
    if claim.check_reference or claim.reference_id is not None:
        want = normalize_control_id(claim.reference_id) if claim.reference_id else None
        if want != row["reference_element_id"]:
            errors.append(f"reference element mismatch: cited {claim.reference_id!r}, stored "
                          f"{row['reference_original_id']!r}")
    if claim.version is not None and claim.version not in (row["focal_version"],
                                                           row["reference_version"]):
        errors.append(f"version {claim.version!r} is not part of this mapping "
                      f"({row['focal_version']} -> {row['reference_version']})")
    if claim.source_file is not None and claim.source_file != row["source_file"]:
        errors.append(f"source_file mismatch: cited {claim.source_file!r}, stored "
                      f"{row['source_file']!r}")
    return errors


def validate_citations(conn: sqlite3.Connection, claims: list[CitationClaim],
                       allowed: set[str] | None = None) -> list[CitationCheck]:
    """Validate each claim against the database. If `allowed` is given (the citation IDs in an
    evidence bundle), citing anything outside it is an error too."""
    results = []
    for claim in claims:
        cid = claim.citation_id
        errors: list[str] = []
        if cid.startswith(CHUNK_PREFIX):
            errors = _check_chunk(conn, claim, cid[len(CHUNK_PREFIX):])
        elif cid.startswith(XWALK_PREFIX):
            try:
                errors = _check_xwalk(conn, claim, int(cid[len(XWALK_PREFIX):]))
            except ValueError:
                errors = [f"malformed crosswalk citation {cid!r}"]
        else:
            errors = [f"unrecognised citation format {cid!r}"]
        if allowed is not None and cid not in allowed:
            errors.append("citation is not part of the supplied evidence bundle")
        results.append(CitationCheck(cid, not errors, errors))
    return results
