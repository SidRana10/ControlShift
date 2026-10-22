"""PyMuPDF line extraction with header/footer removal and heading detection."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .errors import IngestionError

HEADER_MAX_Y = 65.0
FOOTER_MARGIN = 60.0


@dataclass
class Line:
    text: str
    page: int  # 1-based
    x0: float
    y0: float
    bold: bool
    size: float


@dataclass
class Page:
    number: int  # 1-based
    printed: str | None
    lines: list[Line]
    width: float
    height: float


def open_pdf(path: Path) -> pymupdf.Document:
    if not path.is_file():
        raise IngestionError(f"PDF not found: {path}")
    try:
        doc = pymupdf.open(path)
    except Exception as exc:  # pymupdf raises several error types
        raise IngestionError(f"Cannot open {path.name} as a PDF: {exc}") from exc
    if not doc.is_pdf:
        raise IngestionError(f"{path.name} is not a PDF")
    if doc.page_count == 0:
        raise IngestionError(f"{path.name} has no pages")
    return doc


def extract_pages(path: Path) -> list[Page]:
    doc = open_pdf(path)
    pages: list[Page] = []
    for i, page in enumerate(doc, start=1):
        height = page.rect.height
        lines: list[Line] = []
        printed: str | None = None
        for block in page.get_text("dict")["blocks"]:
            for ln in block.get("lines", []):
                text = "".join(s["text"] for s in ln["spans"]).strip()
                if not text:
                    continue
                x0, y0, _, y1 = ln["bbox"]
                if y1 <= HEADER_MAX_Y or y0 >= height - FOOTER_MARGIN:
                    if re.fullmatch(r"\d{1,3}", text):
                        printed = text
                    continue
                first = ln["spans"][0]
                lines.append(
                    Line(text, i, x0, y0, "Bold" in first["font"], round(first["size"], 1))
                )
        lines.sort(key=lambda ln: (round(ln.y0), ln.x0))
        pages.append(Page(i, printed, lines, page.rect.width, height))
    if not any(p.lines for p in pages):
        raise IngestionError(f"{path.name} contains no extractable text (scanned PDF?)")
    return pages


HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*\.?|Appendix [A-Z][.:]?)(\s+\S.*)?$")


def iter_headings(lines: list[Line]):
    """Yield (index, heading_text, level) for bold numbered headings.

    Handles headings split over two bold lines ("1.2" then "Risk Management ...").
    """
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = HEADING_RE.match(ln.text) if (
            ln.bold and not ln.text.startswith(("Figure", "Table")) and "...." not in ln.text
        ) else None
        if m:
            text, consumed = ln.text, 1
            if not m.group(2) and i + 1 < len(lines) and lines[i + 1].bold:
                text, consumed = f"{ln.text} {lines[i + 1].text}", 2
            number = m.group(1).rstrip(".:")
            level = 1 if number.startswith("Appendix") else number.count(".") + 1
            if number.endswith(".0"):
                level = 1
            yield i, re.sub(r"\s+", " ", text).strip(), level, consumed
            i += consumed
        else:
            i += 1
