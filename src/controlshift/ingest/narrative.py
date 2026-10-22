"""Section-aware chunking of narrative (non-Core-table) text."""
from __future__ import annotations

import re

from .models import SUBCATEGORY_RE, Chunk, clean_text, stable_id
from .pdf import Line, Page, iter_headings

MAX_CHARS = 1500
MIN_CHARS = 200  # a trailing chunk shorter than this is merged into the previous one
BULLET_RE = re.compile(r"^[•o]\s|^[-]")
DOT_LEADER_RE = re.compile(r"\.{4,}\s*\d*$")
GAP_FACTOR = 1.45


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+(?=[A-Z“\"(])", text)


def _pack(paragraphs: list[tuple[str, int, str | None]]) -> list[tuple[str, int, str | None]]:
    """Greedily pack (text, page, printed) paragraphs into <= MAX_CHARS chunks."""
    pieces: list[tuple[str, int, str | None]] = []
    for text, page, printed in paragraphs:
        if len(text) <= MAX_CHARS:
            pieces.append((text, page, printed))
            continue
        buf = ""
        for sent in _sentences(text):
            if buf and len(buf) + 1 + len(sent) > MAX_CHARS:
                pieces.append((buf, page, printed))
                buf = sent
            else:
                buf = f"{buf} {sent}".strip()
        if buf:
            pieces.append((buf, page, printed))
    chunks: list[tuple[str, int, str | None]] = []
    for text, page, printed in pieces:
        if chunks and len(chunks[-1][0]) + 1 + len(text) <= MAX_CHARS:
            chunks[-1] = (f"{chunks[-1][0]}\n{text}", chunks[-1][1], chunks[-1][2])
        else:
            chunks.append((text, page, printed))
    if len(chunks) > 1 and len(chunks[-1][0]) < MIN_CHARS:
        last = chunks.pop()
        chunks[-1] = (f"{chunks[-1][0]}\n{last[0]}", chunks[-1][1], chunks[-1][2])
    return chunks


def chunk_narrative(
    pages: list[Page], version: str, source_file: str, skip_pages: set[int]
) -> list[Chunk]:
    stack: list[tuple[int, str]] = []
    out: list[Chunk] = []
    paragraphs: list[tuple[str, int, str | None]] = []
    cur: list[str] = []
    cur_meta: tuple[int, str | None] | None = None
    prev: Line | None = None

    def end_paragraph() -> None:
        nonlocal cur, cur_meta
        if cur and cur_meta:
            text = clean_text("\n".join(cur))
            if text:
                paragraphs.append((text, cur_meta[0], cur_meta[1]))
        cur, cur_meta = [], None

    def flush_section() -> None:
        end_paragraph()
        section = " > ".join(t for _, t in stack) or "(front matter)"
        for text, page, printed in _pack(paragraphs):
            out.append(
                Chunk(
                    chunk_id=stable_id(version, "text", section, text),
                    version=version, source_file=source_file, chunk_type="text",
                    page=page, printed_page=printed, section=section, text=text,
                    mentioned_controls=sorted({m.group(0) for m in SUBCATEGORY_RE.finditer(text)}),
                )
            )
        paragraphs.clear()

    for page in pages:
        if page.number in skip_pages:
            continue
        heads = {i: (t, lvl, n) for i, t, lvl, n in iter_headings(page.lines)}
        skip_idx: set[int] = set()
        prev = None
        for idx, ln in enumerate(page.lines):
            if idx in skip_idx:
                continue
            if idx in heads:
                title, level, consumed = heads[idx]
                skip_idx.update(range(idx, idx + consumed))
                flush_section()
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, title))
                prev = None
                continue
            if DOT_LEADER_RE.search(ln.text):
                continue
            new_para = (
                prev is None
                or BULLET_RE.match(ln.text) is not None
                or ln.y0 - prev.y0 > GAP_FACTOR * max(ln.size, 1.0)
            )
            if new_para:
                end_paragraph()
                cur_meta = (page.number, page.printed)
            elif cur_meta is None:
                cur_meta = (page.number, page.printed)
            cur.append(re.sub(r"^[-•]\s*", "• ", ln.text))
            prev = ln
        prev = None
        end_paragraph()
    flush_section()
    return out
