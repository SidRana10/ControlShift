"""Read-only catalog routes: browse and inspect the authoritative NIST records (no LLM, no retrieval)."""
from __future__ import annotations

import re
from typing import Literal

import anyio.to_thread
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..store.queries import KnowledgeStore
from ..store.schema import FOCAL_VERSION
from .schemas import ErrorResponse

Version = Literal["1.1", "2.0"]
Level = Literal["function", "category", "subcategory"]

router = APIRouter(prefix="/catalog", tags=["catalog"])
ERRORS = {404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}
_ID = re.compile(r"^[A-Za-z]{2}(?:\.[A-Za-z]{2}(?:-\d{1,2})?)?$")


class ElementCounts(BaseModel):
    function: int
    category: int
    subcategory: int


class SourceDocument(BaseModel):
    source_file: str
    kind: str
    sha256: str
    bytes: int
    pages: int | None


class VersionInfo(BaseModel):
    version: Version
    name: str
    source_document: SourceDocument
    counts: ElementCounts
    total_elements: int


class VersionList(BaseModel):
    versions: list[VersionInfo]


class ElementSummary(BaseModel):
    version: Version
    element_id: str
    original_id: str
    level: Level
    name: str | None
    description: str | None
    function_id: str
    category_id: str | None
    parent_id: str | None


class ElementList(BaseModel):
    count: int
    elements: list[ElementSummary]


class ChunkProvenance(BaseModel):
    chunk_id: str
    page: int
    printed_page: str | None
    section: str


class Provenance(BaseModel):
    source_document: SourceDocument
    chunk: ChunkProvenance


class CrosswalkEntry(BaseModel):
    """One original workbook row, unmerged. `mapping_type` is assigned at ingest from the row's
    reference cell and comment; it is not a column of the NIST workbook."""

    excel_row: int
    sheet: str
    source_file: str
    focal_version: Version
    focal_element_id: str
    focal_original_id: str
    focal_description: str | None
    reference_version: Version
    reference_element_id: str | None
    reference_original_id: str | None
    reference_description: str | None
    comments: str | None
    strength: str | None
    mapping_type: Literal["mapped", "new_in_2_0", "unmapped"]


class CrosswalkSummary(BaseModel):
    """Derived interpretation computed by this API; none of these fields exist in the workbook."""

    derived: Literal[True] = True
    status: Literal["mapped_only", "new_in_2_0_only", "mapped_and_new_in_2_0",
                    "no_crosswalk_reference", "unclassified"]
    mapped_row_count: int
    new_in_2_0_row_count: int
    excel_rows: list[int]
    note: str


class Crosswalk(BaseModel):
    direction: Literal["CSF 2.0 (focal) -> CSF 1.1 (reference)"] = "CSF 2.0 (focal) -> CSF 1.1 (reference)"
    queried_role: Literal["focal", "reference"]
    lookup: Literal["forward", "reverse"]
    entries: list[CrosswalkEntry]
    summary: CrosswalkSummary


class ElementDetail(ElementSummary):
    parent: ElementSummary | None
    children: list[ElementSummary]
    informative_references: list[str]
    provenance: Provenance
    crosswalk: Crosswalk


def summarize_crosswalk(rows: list[dict]) -> dict:
    """Derived label over raw rows. Rows are never merged; the rows themselves stay authoritative.

    Mirrors (does not replace) the 'mapped and new' detection in evidence/assemble.py, which is
    left untouched; sharing one helper is deferred.
    """
    mapped = sum(r["mapping_type"] == "mapped" for r in rows)
    new = sum(r["mapping_type"] == "new_in_2_0" for r in rows)
    if not rows:
        status, note = "no_crosswalk_reference", (
            "No official crosswalk row references this element. This is not a statement that "
            "it was removed or has no conceptual counterpart.")
    elif mapped and new:
        status, note = "mapped_and_new_in_2_0", (
            "The workbook holds both mapped row(s) and a 'Conceptually new in 2.0' row for this "
            "element. Both are reported; neither is preferred.")
    elif mapped and mapped == len(rows):
        status, note = "mapped_only", "All official rows for this element carry a reference element."
    elif new and new == len(rows):
        status, note = "new_in_2_0_only", "The only official row(s) are marked conceptually new in 2.0."
    else:
        status, note = "unclassified", "Rows include a type this summary does not interpret."
    return {"status": status, "mapped_row_count": mapped, "new_in_2_0_row_count": new,
            "excel_rows": [r["excel_row"] for r in rows], "note": note}


def _not_found(message: str) -> JSONResponse:
    return JSONResponse(status_code=404, content={
        "error": {"code": "not_found", "message": message, "details": None}})


def _versions(db_path) -> dict:
    with KnowledgeStore(db_path) as s:
        out = []
        for v in s.list_versions():
            counts = v["counts"]
            doc = {k: v[k] for k in ("source_file", "kind", "sha256", "bytes", "pages")}
            out.append({"version": v["version"], "name": v["name"], "source_document": doc,
                        "counts": counts, "total_elements": sum(counts.values())})
        return {"versions": out}


def _detail(db_path, version: str, element_id: str) -> dict | None:
    with KnowledgeStore(db_path) as s:
        rec = s.get_control(element_id, version)
        if rec is None:
            return None
        eid = rec["element_id"]
        parent = s.get_control(rec["parent_id"], version) if rec["parent_id"] else None
        own = next(c for c in s.get_evidence(eid, version) if c["relation"] == "control")
        forward = version == FOCAL_VERSION
        rows = s.mappings_2_0_to_1_1(eid) if forward else s.mappings_1_1_to_2_0(eid)
        return {
            **{k: v for k, v in rec.items() if k != "informative_references"},
            "parent": parent, "children": s.list_children(eid, version),
            "informative_references": rec["informative_references"],
            "provenance": {"source_document": s.get_source_document(own["source_file"]),
                           "chunk": own},
            "crosswalk": {"queried_role": "focal" if forward else "reference",
                          "lookup": "forward" if forward else "reverse",
                          "entries": rows, "summary": summarize_crosswalk(rows)}}


@router.get("/versions", response_model=VersionList)
async def catalog_versions(request: Request):
    return await anyio.to_thread.run_sync(_versions, request.app.state.services.db_path)


@router.get("/elements", response_model=ElementList, responses=ERRORS)
async def catalog_elements(
        request: Request, version: Version | None = None, level: Level | None = None,
        function: str | None = Query(None, pattern=r"^[A-Za-z]{2}$"),
        category: str | None = Query(None, pattern=r"^[A-Za-z]{2}\.[A-Za-z]{2}$"),
        q: str | None = Query(None, max_length=200)):
    def run():
        with KnowledgeStore(request.app.state.services.db_path) as s:
            return s.list_elements(
                version=version, level=level, function_id=function and function.upper(),
                category_id=category and category.upper(), q=(q or "").strip() or None)

    rows = await anyio.to_thread.run_sync(run)
    return {"count": len(rows), "elements": rows}


@router.get("/elements/{version}/{element_id}", response_model=ElementDetail, responses=ERRORS)
async def catalog_element(request: Request, version: Version, element_id: str):
    eid = element_id.strip().upper()
    detail = None
    if _ID.match(eid):
        detail = await anyio.to_thread.run_sync(
            _detail, request.app.state.services.db_path, version, eid)
    if detail is None:
        return _not_found(f"{element_id} not found in CSF {version}")
    return detail


__all__ = ["router"]
