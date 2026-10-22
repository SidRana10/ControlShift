from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

FUNCTION_NAMES = {
    "GV": "Govern",
    "ID": "Identify",
    "PR": "Protect",
    "DE": "Detect",
    "RS": "Respond",
    "RC": "Recover",
}

SUBCATEGORY_RE = re.compile(r"\b([A-Z]{2})\.([A-Z]{2})-(\d{1,2})\b")
CATEGORY_RE = re.compile(r"\b([A-Z]{2})\.([A-Z]{2})\b(?!-)")


def normalize_control_id(raw: str) -> str:
    """'PR.AT-1' -> 'PR.AT-01'; function/category IDs are returned unchanged."""
    raw = raw.strip()
    m = re.fullmatch(r"([A-Z]{2}\.[A-Z]{2})-(\d{1,2})", raw)
    return f"{m.group(1)}-{int(m.group(2)):02d}" if m else raw


def control_level(control_id: str) -> str:
    if "-" in control_id:
        return "subcategory"
    return "category" if "." in control_id else "function"


@dataclass
class Chunk:
    chunk_id: str
    version: str  # "1.1" | "2.0"
    source_file: str
    chunk_type: str  # function | category | subcategory | text
    page: int  # 1-based PDF page index (start page)
    printed_page: str | None
    section: str  # " > "-joined heading path
    text: str
    control_id: str | None = None
    function_id: str | None = None
    category_id: str | None = None
    informative_references: list[str] = field(default_factory=list)
    mentioned_controls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["char_count"] = len(self.text)
        return d


def stable_id(version: str, kind: str, *parts: str) -> str:
    """Deterministic ID: control chunks use their control ID; text chunks hash content."""
    if kind in ("function", "category", "subcategory"):
        return f"csf{version}:{kind}:{parts[0]}"
    digest = hashlib.sha1("\x1f".join((version, *parts)).encode()).hexdigest()[:12]
    return f"csf{version}:text:{digest}"


def clean_text(text: str) -> str:
    text = re.sub(r"-\n(?=[a-z])", "-", text)  # keep hyphen of compounds broken at line end
    return re.sub(r"\s+", " ", text).strip()
