"""Evidence-context assembly under a character budget.

Priority: (1) exact control records and (2) official crosswalk rows are always kept (their
descriptions are trimmed before anything is dropped); (3) retrieved passages fill what is left,
interleaved across versions so comparisons keep both sides. Identical text within one version is
merged, but every merged citation stays citable.
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field

from ..evidence.bundle import EvidenceBundle

MIN_PASSAGE_CHARS = 300
INJECTION_PATTERNS = [
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)",
    r"disregard (?:all |any |the )?(?:previous|prior|above|earlier)",
    r"(?:reveal|print|show|repeat) (?:your |the )?(?:system )?(?:prompt|instructions)",
    r"you are now\b", r"\bnew instructions?\b", r"\bsystem prompt\b",
    r"(?:api[_ ]?key|password|secret)\b.{0,20}(?:is|=|:)", r"</?\s*(?:evidence|system|assistant)\b",
]
_INJECTION = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


@dataclass
class EvidenceContext:
    text: str
    allowed_citations: set[str]
    included: list[str]
    omitted: list[str] = field(default_factory=list)
    truncated: list[str] = field(default_factory=list)
    merged_duplicates: dict[str, list[str]] = field(default_factory=dict)
    injection_flags: list[dict] = field(default_factory=list)
    mandatory_over_budget: bool = False
    chars: int = 0

    def summary(self) -> dict:
        return {"included": self.included, "omitted": self.omitted, "truncated": self.truncated,
                "merged_duplicates": self.merged_duplicates, "chars": self.chars,
                "mandatory_over_budget": self.mandatory_over_budget}


def _attr(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _body(t: str, limit: int | None) -> tuple[str, bool]:
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
    cut = limit is not None and len(t) > limit
    return html.escape(t[:limit] + (" [...truncated]" if cut else "") if limit else t,
                       quote=False), cut


def _norm_text(t: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", t).strip().lower().encode()).hexdigest()


def _render_chunk(item: dict, kind: str, limit: int | None, also: list[str]) -> tuple[str, bool]:
    body, cut = _body(item["text"], limit)
    attrs = (f'id="{_attr(item["citation_id"])}" kind="{kind}" version="{_attr(item["version"])}" '
             f'control="{_attr(item.get("control_id"))}" source="{_attr(item["source_file"])}" '
             f'page="{_attr(item["page"])}" section="{_attr(item["section"])}"')
    if also:
        attrs += f' identical_text_also_cited_as="{_attr(",".join(also))}"'
    return f"<evidence {attrs}>{body}</evidence>", cut


def _render_xwalk(r: dict, limit: int | None) -> str:
    fd, _ = _body(r["focal_description"] or "", limit)
    rd, _ = _body(r["reference_description"] or "", limit)
    attrs = (f'id="{_attr(r["citation_id"])}" kind="official_crosswalk" '
             f'direction="CSF 2.0 (focal) -> CSF 1.1 (reference)" '
             f'focal="{_attr(r["focal_id"])}" reference="{_attr(r["reference_id"])}" '
             f'mapping_type="{_attr(r["mapping_type"])}" comments="{_attr(r["comments"])}" '
             f'strength="{_attr(r["strength"])}" excel_row="{_attr(r["excel_row"])}"')
    return (f"<evidence {attrs}>focal_description: {fd}\nreference_description: {rd}</evidence>")


def build_context(bundle: EvidenceBundle, budget_chars: int = 12000,
                  max_passage_chars: int = 1500) -> EvidenceContext:
    blocks: list[str] = []
    ctx = EvidenceContext(text="", allowed_citations=set(), included=[])
    seen_text: dict[tuple[str, str], str] = {}  # (version, text hash) -> citation id kept

    for rec in bundle.control_records:  # 1. exact control records (always kept)
        h = (rec["version"], _norm_text(rec["text"]))
        seen_text[h] = rec["citation_id"]
        block, cut = _render_chunk(rec, "control_record", None, [])
        blocks.append(block)
        ctx.included.append(rec["citation_id"])
    for r in bundle.crosswalk_records:  # 2. official mapping rows (always kept)
        blocks.append(_render_xwalk(r, None))
        ctx.included.append(r["citation_id"])
    used = sum(len(b) for b in blocks)
    if used > budget_chars:  # trim descriptions before dropping anything mandatory
        ctx.mandatory_over_budget = True
        blocks = [_render_xwalk(r, 200) for r in bundle.crosswalk_records]
        blocks = [_render_chunk(rec, "control_record", 400, [])[0]
                  for rec in bundle.control_records] + blocks
        used = sum(len(b) for b in blocks)
        ctx.truncated += ["(mandatory records trimmed to fit the budget)"]

    # 3. passages, interleaved across versions in retrieval order
    by_version: dict[str, list[dict]] = {}
    for p in bundle.passages:
        by_version.setdefault(p["version"], []).append(p)
    queues = [by_version[v] for v in sorted(by_version)]
    ordered: list[dict] = []
    while any(queues):
        for q in queues:
            if q:
                ordered.append(q.pop(0))
    for p in ordered:
        key = (p["version"], _norm_text(p["text"]))
        if key in seen_text:  # same text, same version: merge but keep it citable
            keeper = seen_text[key]
            ctx.merged_duplicates.setdefault(keeper, []).append(p["citation_id"])
            continue
        remaining = budget_chars - used
        if remaining < MIN_PASSAGE_CHARS:
            ctx.omitted.append(p["citation_id"])
            continue
        limit = min(max_passage_chars, max(MIN_PASSAGE_CHARS, remaining - 400))
        block, cut = _render_chunk(p, "retrieved_passage", limit, [])
        if len(block) > remaining:
            ctx.omitted.append(p["citation_id"])
            continue
        if cut:
            ctx.truncated.append(p["citation_id"])
        if m := _INJECTION.search(p["text"]):
            ctx.injection_flags.append({"citation_id": p["citation_id"], "match": m.group(0)})
        seen_text[key] = p["citation_id"]
        blocks.append(block)
        ctx.included.append(p["citation_id"])
        used += len(block)

    if ctx.merged_duplicates:  # tell the model which citation IDs share a block
        for keeper, dupes in ctx.merged_duplicates.items():
            for i, b in enumerate(blocks):
                if f'id="{_attr(keeper)}"' in b:
                    blocks[i] = b.replace(" section=", f' identical_text_also_cited_as='
                                          f'"{_attr(",".join(dupes))}" section=', 1)
    ctx.allowed_citations = set(ctx.included) | {d for v in ctx.merged_duplicates.values()
                                                 for d in v}
    ctx.text = "\n".join(blocks)
    ctx.chars = len(ctx.text)
    return ctx
