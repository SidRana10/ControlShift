from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .corpus import Doc


@dataclass
class Hit:
    rank: int
    score: float
    mode: str  # bm25 | dense | hybrid | hybrid_rerank
    chunk_id: str
    version: str
    control_id: str | None
    chunk_type: str
    source_file: str
    page: int
    printed_page: str | None
    section: str
    text: str
    matched_passage: str | None = None  # dense: the sub-passage that matched best
    components: dict = field(default_factory=dict)  # per-stage {rank, score} for debugging

    @classmethod
    def from_doc(cls, doc: Doc, rank: int, score: float, mode: str) -> Hit:
        return cls(rank=rank, score=float(score), mode=mode, chunk_id=doc.chunk_id,
                   version=doc.version, control_id=doc.control_id, chunk_type=doc.chunk_type,
                   source_file=doc.source_file, page=doc.page, printed_page=doc.printed_page,
                   section=doc.section, text=doc.text)

    def to_dict(self) -> dict:
        return asdict(self)
