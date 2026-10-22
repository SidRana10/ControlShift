"""Parse the official NIST CSF 2.0 <-> 1.1 transition workbook, preserving original rows."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .errors import IngestionError
from .models import control_level, normalize_control_id

SHEET = "Relationships"
# Original header -> output key. In this workbook the focal document is CSF 2.0 and the
# reference document is CSF 1.1 (verified against the element IDs, see manifest).
COLUMNS = {
    "focal document element": "focal_id",
    "focal document element description": "focal_description",
    "reference document element": "reference_id",
    "reference document element description (optional)": "reference_description",
    "comments (optional)": "comments",
    "strength of relationship (optional)": "strength",
}


def _canon(header: object) -> str:
    return " ".join(str(header).lower().split())


def _cell(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def parse_crosswalk(path: Path) -> list[dict]:
    if not path.is_file():
        raise IngestionError(f"Excel crosswalk not found: {path}")
    try:
        df = pd.read_excel(path, sheet_name=SHEET, dtype=object, engine="openpyxl")
    except ValueError as exc:  # missing sheet
        raise IngestionError(f"{path.name}: sheet '{SHEET}' not readable ({exc})") from exc
    except Exception as exc:
        raise IngestionError(f"Cannot read {path.name} as an Excel workbook: {exc}") from exc

    by_canon = {_canon(c): c for c in df.columns}
    missing = [h for h in COLUMNS if h not in by_canon]
    if missing:
        raise IngestionError(f"{path.name}: missing expected columns {missing}")
    if df.empty:
        raise IngestionError(f"{path.name}: sheet '{SHEET}' has no data rows")

    rows: list[dict] = []
    for i, (_, rec) in enumerate(df.iterrows()):
        row = {key: _cell(rec[by_canon[h]]) for h, key in COLUMNS.items()}
        if row["focal_id"] is None:
            raise IngestionError(f"{path.name}: row {i + 2} has no focal element")
        comment = (row["comments"] or "").lower()
        row["mapping_type"] = (
            "mapped" if row["reference_id"]
            else "new_in_2_0" if "new" in comment
            else "unmapped"
        )
        row["focal_level"] = control_level(row["focal_id"])
        row["reference_level"] = control_level(row["reference_id"]) if row["reference_id"] else None
        row["focal_id_normalized"] = normalize_control_id(row["focal_id"])
        row["reference_id_normalized"] = (
            normalize_control_id(row["reference_id"]) if row["reference_id"] else None
        )
        row["excel_row"] = i + 2  # header is row 1
        row["sheet"] = SHEET
        row["source_file"] = path.name
        rows.append(row)
    return rows
