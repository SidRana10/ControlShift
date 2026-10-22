"""Deterministic, rule-based query planner. No model calls; ambiguity is recorded, not resolved."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from ..ingest.models import FUNCTION_NAMES, control_level, normalize_control_id

SINGLE_VERSION = "single_version"
CROSS_VERSION = "cross_version_comparison"
CONTROL_MAPPING = "control_mapping"
UNSUPPORTED = "unsupported"

_VERSION_RE = re.compile(
    r"(?<![\w.])(?:(?:csf|nist csf|version|ver\.?|v)\s*)?(1\.1|2\.0)(?![\w.]*\w)", re.IGNORECASE)
_NOT_VERSION_PREFIX = re.compile(r"(section|sec\.|page|p\.|figure|fig\.|table|appendix|§)\s*$",
                                 re.IGNORECASE)
_ID_RE = re.compile(r"(?<![\w.])([A-Za-z]{2})\.([A-Za-z]{2})(?:-(\d{1,2}))?(?![\w])")
_WORD_RE = re.compile(r"[a-z0-9']+")

# Words that, on their own, are enough to ask for a comparison. Incidental words such as "new",
# "changed" or "between" are deliberately NOT here: "new technologies" or "changes in the threat
# landscape" are not requests to compare framework versions.
STRONG_COMPARISON_CUES = {"compare", "compared", "comparison", "difference", "differences",
                          "differ", "differs", "versus", "vs", "evolved", "evolve", "diff"}
MAPPING_CUES = {"map", "maps", "mapped", "mapping", "mappings", "crosswalk", "equivalent",
                "equivalents", "correspond", "corresponds", "corresponding", "counterpart",
                "replace", "replaced", "replaces", "replacement", "supersedes", "superseded"}
REMOVAL_CUES = {"removed", "dropped", "retired", "deleted", "deprecated"}

# Idioms that ask how the framework itself changed between versions.
_CHANGE_IDIOMS = [
    re.compile(r"\bwhat(?:'s|\s+(?:is|are|was|were|has\s+been|have\s+been))\s+new\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:\s+(?:has|have|was|were|is|are))?(?:\s+been)?\s+"
               r"(?:changed|added|introduced|removed|dropped|retired|moved|relocated)\b", re.IGNORECASE),
    re.compile(r"\b(?:which|how many)\b[^.?]*\b(?:are|were|is|was)\s+"
               r"(?:new|added|removed|dropped|introduced|retired)\b", re.IGNORECASE),
    re.compile(r"\b(?:new|added|introduced|removed|dropped|retired)\s+(?:in|since|from)\s+"
               r"(?:csf\s*|version\s*|v)?\d", re.IGNORECASE),
    re.compile(r"\b(?:changed?|moved|relocated|renumbered|replaced)\s+(?:from|since|between)\b",
               re.IGNORECASE),
]
_NEW_WORDS = re.compile(r"\b(?:new|added|introduced)\b", re.IGNORECASE)
RELATIVE_VERSION_TERMS = {"old", "older", "previous", "prior", "earlier", "original", "latest",
                          "current", "newer", "legacy"}


@dataclass
class ControlRef:
    raw: str  # as written in the question
    normalized: str  # zero-padded form used as key in the database
    level: str  # function | category | subcategory


@dataclass
class QueryPlan:
    question: str
    query_type: str
    explicit_versions: list[str] = field(default_factory=list)
    controls: list[ControlRef] = field(default_factory=list)
    cues: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)  # carried into the bundle unchanged

    def to_dict(self) -> dict:
        return asdict(self)


def extract_versions(question: str) -> list[str]:
    found: list[str] = []
    for m in _VERSION_RE.finditer(question):
        if _NOT_VERSION_PREFIX.search(question[: m.start()]):
            continue
        if m.group(1) not in found:
            found.append(m.group(1))
    return sorted(found)


def extract_controls(question: str) -> tuple[list[ControlRef], list[str]]:
    """(control references, unrecognised identifier-like strings)."""
    refs: list[ControlRef] = []
    unknown: list[str] = []
    for m in _ID_RE.finditer(question):
        fn, cat, num = m.group(1).upper(), m.group(2).upper(), m.group(3)
        raw = m.group(0)
        if fn not in FUNCTION_NAMES:
            if num:  # looks like a control ID but the function code does not exist
                unknown.append(raw)
            continue
        norm = normalize_control_id(f"{fn}.{cat}-{num}" if num else f"{fn}.{cat}")
        if all(r.normalized != norm for r in refs):
            refs.append(ControlRef(raw=raw, normalized=norm, level=control_level(norm)))
    return refs, unknown


def plan_query(question: str) -> QueryPlan:
    q = (question or "").strip()
    words = set(_WORD_RE.findall(q.lower()))
    versions = extract_versions(q)
    controls, unknown_ids = extract_controls(q)
    strong = sorted(words & STRONG_COMPARISON_CUES)
    mapping = sorted(words & MAPPING_CUES)
    idiom = next((m.group(0) for p in _CHANGE_IDIOMS if (m := p.search(q))), None)
    cues = strong + mapping + (["change_idiom"] if idiom else []) + (
        ["change:new"] if idiom and _NEW_WORDS.search(idiom) else [])
    notes: list[str] = []

    if not (words or controls):
        msg = "The question is empty or contains no searchable terms."
        return QueryPlan(q, UNSUPPORTED, uncertainties=[msg])
    for ident in unknown_ids:
        notes.append(f"'{ident}' looks like a control ID but its function code is not a CSF "
                     "function (GV, ID, PR, DE, RS, RC); it was ignored.")
    if words & RELATIVE_VERSION_TERMS and not versions:
        notes.append("The question uses relative version wording (e.g. 'old', 'previous', "
                     "'latest') without naming a version; no version was assumed.")

    # A change idiom ("what changed", "new in 2.0") only means a version comparison when the
    # question is anchored to the framework: a named version or a control ID.
    anchored_change = bool(idiom) and bool(versions or controls)
    comparison = bool(strong) or len(versions) == 2 or anchored_change
    if idiom and not anchored_change and not strong:
        notes.append("The wording ('" + idiom.strip() + "') could ask how the framework changed "
                     "between versions, but no version or control is named; it is treated as a "
                     "single-version question and no comparison was assumed.")

    if controls and (mapping or comparison):
        qtype = CONTROL_MAPPING
    elif controls:
        qtype = SINGLE_VERSION  # exact control lookup
    elif comparison or mapping:
        qtype = CROSS_VERSION
        if len(versions) == 1:
            notes.append(f"Only CSF {versions[0]} is named for a comparison; the comparison "
                         "baseline/target was not stated, so both versions are searched.")
    else:
        qtype = SINGLE_VERSION
        if not versions:
            notes.append("No framework version was named; evidence is gathered from both "
                         "CSF 1.1 and CSF 2.0 separately.")
    if words & REMOVAL_CUES:
        notes.append("The crosswalk has no explicit 'removed' status; absence of a mapping "
                     "must not be read as removal.")
    return QueryPlan(q, qtype, versions, controls, cues, notes)
