"""Extract Function / Category / Subcategory chunks from the two Core appendices."""
from __future__ import annotations

import re

from .models import FUNCTION_NAMES, Chunk, clean_text, stable_id
from .pdf import Page

SUB_ID = r"[A-Z]{2}\.[A-Z]{2}-\d{1,2}"

# ---------------------------------------------------------------- CSF 2.0 --------
# Appendix A is a bulleted list:
#   GOVERN (GV): <text>
#   • Organizational Context (GV.OC): <text>
#   o GV.OC-01: <text>
_V2_FUNCTION = re.compile(r"^([A-Z]{4,})\s+\(([A-Z]{2})\):\s*(.*)")
_V2_CATEGORY = re.compile(r"^[•]\s*(.+?)\s+\(([A-Z]{2}\.[A-Z]{2})\):\s*(.*)")
_V2_SUB = re.compile(rf"^o\s+({SUB_ID}):\s*(.*)")


def parse_csf20_core(pages: list[Page], source_file: str) -> list[Chunk]:
    entries: list[dict] = []
    current: dict | None = None
    for page in pages:
        for ln in page.lines:
            text = ln.text
            if ln.bold and not _V2_FUNCTION.match(text):
                current = None  # a heading ends any open entry (e.g. "Appendix B")
                continue
            if m := _V2_SUB.match(text):
                current = {"level": "subcategory", "id": m.group(1), "name": None,
                           "text": [m.group(2)], "page": page.number, "printed": page.printed}
            elif m := _V2_CATEGORY.match(text):
                current = {"level": "category", "id": m.group(2), "name": m.group(1),
                           "text": [m.group(3)], "page": page.number, "printed": page.printed}
            elif (m := _V2_FUNCTION.match(text)) and m.group(2) in FUNCTION_NAMES:
                current = {"level": "function", "id": m.group(2), "name": m.group(1).title(),
                           "text": [m.group(3)], "page": page.number, "printed": page.printed}
            elif current is not None:
                current["text"].append(text)
                continue
            else:
                continue
            entries.append(current)
    return [_entry_to_chunk(e, "2.0", source_file) for e in entries]


def _entry_to_chunk(e: dict, version: str, source_file: str, refs: list[str] | None = None) -> Chunk:
    cid = e["id"]
    fn = cid[:2]
    cat = cid[:5] if e["level"] != "function" else None
    body = clean_text("\n".join(e["text"]))
    if e["level"] == "function":
        section = f"Core > {FUNCTION_NAMES[fn]} ({fn})"
        text = f"{FUNCTION_NAMES[fn].upper()} ({fn})" + (f": {body}" if body else "")
    elif e["level"] == "category":
        section = f"Core > {FUNCTION_NAMES[fn]} ({fn}) > {cid}"
        text = f"{e['name']} ({cid}): {body}"
    else:
        section = f"Core > {FUNCTION_NAMES[fn]} ({fn}) > {cid}"
        text = f"{cid}: {body}"
    return Chunk(
        chunk_id=stable_id(version, e["level"], cid), version=version, source_file=source_file,
        chunk_type=e["level"], page=e["page"], printed_page=e["printed"], section=section,
        text=text, control_id=cid, function_id=fn, category_id=cat,
        informative_references=refs or [],
    )


# ---------------------------------------------------------------- CSF 1.1 --------
# Appendix A Table 2 is a 4-column table (function | category | subcategory | refs).
# Columns are separated by x position; a subcategory and its references share a top y.
_V1_SUB = re.compile(rf"^({SUB_ID}):\s*(.*)")
_V1_CAT = re.compile(r"(.+?)\s*\(([A-Z]{2}\.[A-Z]{2})\):\s*(.*)", re.DOTALL)
SUB_X = (300.0, 500.0)
REF_X = 500.0
Y_TOL = 4.0


def _is_core_table_page(page: Page) -> bool:
    texts = {ln.text for ln in page.lines}
    return {"Function", "Category", "Subcategory"} <= texts


def parse_csf11_core(pages: list[Page], source_file: str) -> tuple[list[Chunk], set[int]]:
    """Returns (chunks, set of page numbers that hold the Core table)."""
    table_pages = [p for p in pages if _is_core_table_page(p)]
    cat_lines: list[str] = []
    subs: list[dict] = []
    for page in table_pages:
        body = [ln for ln in page.lines if ln.y0 > 90]  # below the column-header row
        for ln in body:
            if ln.x0 < SUB_X[0] - 1 and ln.x0 > 120:
                cat_lines.append(ln.text)
        # subcategories: start at an ID line in the sub column; continuation until next ID
        sub_col = [ln for ln in body if SUB_X[0] <= ln.x0 < SUB_X[1] - 1]
        for ln in sub_col:
            if m := _V1_SUB.match(ln.text):
                subs.append({"level": "subcategory", "id": m.group(1), "name": None,
                             "text": [m.group(2)], "page": page.number, "printed": page.printed,
                             "y0": ln.y0, "ref_lines": [], "page_obj": page})
            elif subs:  # wrapped text, possibly continued from the previous page
                subs[-1]["text"].append(ln.text)
        # references: lines in the ref column, attached to the sub whose y-range contains them
        page_subs = [s for s in subs if s["page"] == page.number]
        for ln in (x for x in body if x.x0 >= REF_X - 1):
            # refs above the first row of a page continue the previous page's last row
            earlier = [s for s in subs if s["page"] < page.number]
            owner = earlier[-1] if earlier else None
            for s in page_subs:
                if s["y0"] - Y_TOL <= ln.y0:
                    owner = s
            if owner is not None:
                owner["ref_lines"].append(ln.text)

    chunks: list[Chunk] = []
    first_page = {p.number: p for p in table_pages}
    # categories: parse the concatenated category column
    cat_text = " ".join(cat_lines)
    parts = re.split(r"(?<=[.])\s+(?=[A-Z][A-Za-z ,&’'-]+ \([A-Z]{2}\.[A-Z]{2}\):)", cat_text)
    seen_cat = set()
    for part in parts:
        m = _V1_CAT.match(part.strip())
        if not m:
            continue
        cid = m.group(2)
        name = re.sub(r"^Category\s+", "", m.group(1).strip())
        if cid in seen_cat:
            continue
        seen_cat.add(cid)
        pg = _first_page_of_category(table_pages, cid, subs)
        chunks.append(_entry_to_chunk(
            {"level": "category", "id": cid, "name": name, "text": [m.group(3)],
             "page": pg.number, "printed": pg.printed}, "1.1", source_file))
    for s in subs:
        refs = _split_refs(s["ref_lines"])
        chunks.append(_entry_to_chunk(s, "1.1", source_file, refs))
    for fn in sorted({c.function_id for c in chunks if c.function_id}):
        pg = next((first_page[c.page] for c in chunks if c.function_id == fn), table_pages[0])
        chunks.append(_entry_to_chunk(
            {"level": "function", "id": fn, "name": FUNCTION_NAMES[fn], "text": [""],
             "page": pg.number, "printed": pg.printed}, "1.1", source_file))
    chunks.sort(key=lambda c: (c.page, {"function": 0, "category": 1, "subcategory": 2}[c.chunk_type],
                               c.control_id))
    return chunks, {p.number for p in table_pages}


def _first_page_of_category(table_pages, cid, subs):
    for s in subs:
        if s["id"].startswith(cid):
            return s["page_obj"]
    return table_pages[0]


_REF_START = re.compile(r"^(CIS CSC|COBIT 5|ISA 62443|ISO/IEC 27001|NIST SP 800-53)")


def _split_refs(lines: list[str]) -> list[str]:
    """Group wrapped lines into one string per framework reference."""
    refs: list[str] = []
    for text in lines:
        if _REF_START.match(text) or not refs:
            refs.append(text.strip())
        else:
            sep = "" if refs[-1].endswith("-") else " "
            refs[-1] += sep + text.strip()
    return [re.sub(r"\s+", " ", r) for r in refs]
