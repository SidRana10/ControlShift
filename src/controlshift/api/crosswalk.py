"""Read-only browse of the official transition-workbook rows (no LLM, no retrieval).

Not to be confused with POST /compare, the LLM-backed question endpoint. Rows are returned exactly
as stored (reusing the Catalog's CrosswalkEntry model); nothing is merged or inferred.
"""
from __future__ import annotations

import re
from typing import Literal

import anyio.to_thread
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from ..store.queries import KnowledgeStore
from .catalog import CrosswalkEntry
from .schemas import ErrorResponse

router = APIRouter(prefix="/crosswalk", tags=["crosswalk"])
_ID = r"^[A-Za-z]{2}(?:\.[A-Za-z]{2}(?:-\d{1,2})?)?$"
assert re.compile(_ID)


class MappingTypeCounts(BaseModel):
    mapped: int
    new_in_2_0: int
    unmapped: int


class CrosswalkList(BaseModel):
    """`total` counts rows matching every filter; `entries` is one page of them in workbook order.
    `type_counts` counts the rows matching all filters except `type`. `mapping_type` is a
    ControlShift ingest label, not a workbook column."""

    direction: Literal["CSF 2.0 (focal) -> CSF 1.1 (reference)"] = "CSF 2.0 (focal) -> CSF 1.1 (reference)"
    total: int
    count: int
    limit: int
    offset: int
    type_counts: MappingTypeCounts
    entries: list[CrosswalkEntry]


@router.get("", response_model=CrosswalkList, responses={422: {"model": ErrorResponse}})
async def crosswalk_rows(
        request: Request,
        focal: str | None = Query(None, pattern=_ID, description="CSF 2.0 element (exact)"),
        reference: str | None = Query(None, pattern=_ID, description="CSF 1.1 element (exact)"),
        type: Literal["mapped", "new_in_2_0", "unmapped"] | None = None,
        q: str | None = Query(None, max_length=200),
        limit: int = Query(250, ge=1, le=250),
        offset: int = Query(0, ge=0)):
    def run():
        with KnowledgeStore(request.app.state.services.db_path) as s:
            return s.list_crosswalk(focal=focal, reference=reference, mapping_type=type,
                                    q=(q or "").strip() or None, limit=limit, offset=offset)

    total, counts, rows = await anyio.to_thread.run_sync(run)
    return {"total": total, "count": len(rows), "limit": limit, "offset": offset,
            "type_counts": counts, "entries": rows}


__all__ = ["router"]
