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
from ..ingest.models import control_level, normalize_control_id

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
    omitted_records: list[str] = field(default_factory=list)  # official control/crosswalk records left out for space

    def summary(self) -> dict:
        return {"included": self.included, "omitted": self.omitted, "truncated": self.truncated,
                "omitted_records": self.omitted_records, "merged_duplicates": self.merged_duplicates, "chars": self.chars,
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


def _category_of(control_id: str | None) -> str:
    """A subcategory id minus its number gives its category id ('XX.YY-3' -> 'XX.YY'); a category id is returned unchanged."""
    return (control_id or "").rsplit("-", 1)[0]


def _tier(kind: str, item: dict, categories: set[tuple[str, str]], conflict_cites: set[str]) -> int:
    """Selection priority (lower = kept first) when the budget cannot hold everything. Only decides WHAT is kept; the
    kept blocks are always emitted in the canonical order (control records, crosswalk rows, passages)."""
    if kind == "control":
        if item["level"] == "category":
            return 0                                                   # category definitions, both versions
        if (item["version"], _category_of(item["control_id"])) in categories:
            return 1                                                   # canonical definitions inside a compared category
        # a control record outside the compared categories: an exact/requested record in a narrow bundle keeps high priority,
        # but next to compared categories it is mere counterpart grounding (its crosswalk row already quotes it): lowest
        return 7 if categories else 1
    if control_level(normalize_control_id(item["focal_id"] or "")) == "category":
        return 3                                                       # official category-level mappings
    if item["citation_id"] in conflict_cites:
        return 4                                                       # conflicting official rows
    if categories:  # next to compared categories, a row reaching outside them (one end elsewhere) comes after those inside
        ends = [(item["focal_version"], _category_of(item["focal_id"])),
                (item["reference_version"], _category_of(item["reference_id"]))]
        if not all(e in categories for e in ends if e[1]):
            return 6
    return 5                                                           # other official rows


def build_context(bundle: EvidenceBundle, budget_chars: int = 12000,
                  max_passage_chars: int = 1500) -> EvidenceContext:
    """Serialize the evidence for the prompt so that the FINAL text (blocks, attributes and separators) is at most
    `budget_chars`. Official records are never shortened: if they do not all fit, the lowest-priority ones are omitted
    (`ctx.omitted_records`) and the caller reports it. Passages fill what is left and, as before, may be cut with an
    explicit '[...truncated]' marker."""
    ctx = EvidenceContext(text="", allowed_citations=set(), included=[])
    categories = {(r["version"], r["control_id"]) for r in bundle.control_records if r["level"] == "category"}
    conflict_cites = {c for f in bundle.conflicts for c in f.get("citations", [])}

    official: list[tuple[int, int, str, str]] = []  # (tier, canonical index, citation id, block)
    seen_text: dict[tuple[str, str], str] = {}      # (version, text hash) -> citation id of the block that carries it
    for i, rec in enumerate(bundle.control_records):
        seen_text[(rec["version"], _norm_text(rec["text"]))] = rec["citation_id"]
        official.append((_tier("control", rec, categories, conflict_cites), i, rec["citation_id"],
                         _render_chunk(rec, "control_record", None, [])[0]))
    for j, r in enumerate(bundle.crosswalk_records):
        official.append((_tier("xwalk", r, categories, conflict_cites), len(bundle.control_records) + j, r["citation_id"],
                         _render_xwalk(r, None)))

    chosen: dict[str, str] = {}  # citation id -> block, for everything selected
    used = 0

    def cost(block: str) -> int:
        return len(block) + (1 if chosen else 0)  # the newline joining it to the previous block

    for _tier_no, _idx, cid, block in sorted(official, key=lambda t: (t[0], t[1])):
        if used + cost(block) <= budget_chars:
            chosen[cid] = block
            used += cost(block)
    ctx.omitted_records = [c for c in [x[2] for x in sorted(official, key=lambda t: t[1])] if c not in chosen]
    ctx.included = [c for c in [x[2] for x in sorted(official, key=lambda t: t[1])] if c in chosen]

    # passages, interleaved across versions in retrieval order
    by_version: dict[str, list[dict]] = {}
    for p in bundle.passages:
        by_version.setdefault(p["version"], []).append(p)
    queues = [by_version[v] for v in sorted(by_version)]
    ordered: list[dict] = []
    while any(queues):
        for q in queues:
            if q:
                ordered.append(q.pop(0))
    passage_blocks: dict[str, tuple[dict, str, bool]] = {}   # citation id -> (passage, block, truncated)
    for p in ordered:
        key = (p["version"], _norm_text(p["text"]))
        keeper = seen_text.get(key)
        if keeper is not None and keeper in chosen:  # same text, same version: merge but keep it citable
            dupes = ctx.merged_duplicates.get(keeper, []) + [p["citation_id"]]
            old = chosen[keeper]
            new = _with_also(old, dupes)
            if used - len(old) + len(new) <= budget_chars:
                ctx.merged_duplicates[keeper] = dupes
                chosen[keeper] = new
                if keeper in passage_blocks:
                    q_, _b, cut_ = passage_blocks[keeper]
                    passage_blocks[keeper] = (q_, new, cut_)
                used += len(new) - len(old)
            else:
                ctx.omitted.append(p["citation_id"])
            continue
        remaining = budget_chars - used - (1 if chosen else 0)
        if remaining < MIN_PASSAGE_CHARS:
            ctx.omitted.append(p["citation_id"])
            continue
        limit = min(max_passage_chars, max(MIN_PASSAGE_CHARS, remaining - 400))
        block, cut = _render_chunk(p, "retrieved_passage", limit, [])
        if len(block) > remaining:
            ctx.omitted.append(p["citation_id"])
            continue
        if m := _INJECTION.search(p["text"]):
            ctx.injection_flags.append({"citation_id": p["citation_id"], "match": m.group(0)})
        if cut:
            ctx.truncated.append(p["citation_id"])
        seen_text[key] = p["citation_id"]
        chosen[p["citation_id"]] = block
        passage_blocks[p["citation_id"]] = (p, block, cut)
        ctx.included.append(p["citation_id"])
        used += cost(block) if len(chosen) > 1 else len(block)

    canonical = [c for c in [x[2] for x in sorted(official, key=lambda t: t[1])] if c in chosen] + [
        p["citation_id"] for p in ordered if p["citation_id"] in passage_blocks]
    ctx.text = "\n".join(chosen[c] for c in canonical)
    ctx.allowed_citations = set(ctx.included) | {d for v in ctx.merged_duplicates.values() for d in v}
    ctx.mandatory_over_budget = bool(ctx.omitted_records)  # kept name: True when official records had to be left out
    ctx.chars = len(ctx.text)
    assert ctx.chars <= budget_chars or not chosen, "evidence context exceeded its budget"
    return ctx


def _with_also(block: str, dupes: list[str]) -> str:
    """Block with identical_text_also_cited_as set to `dupes` (replacing an earlier value)."""
    block = re.sub(r' identical_text_also_cited_as="[^"]*"', "", block, count=1)
    return block.replace(" section=", f' identical_text_also_cited_as="{_attr(",".join(dupes))}" section=', 1)
