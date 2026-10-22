"""Evaluation dataset schema, loading and label-integrity validation against the database."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..store.schema import connect

CATEGORIES = ["exact_id", "semantic", "version_specific", "cross_version"]
DIFFICULTIES = ["easy", "medium", "hard"]
STATUSES = ["final", "provisional"]
PROVENANCE = "ai_curated_source_checked"  # labels written by an AI from the source text
GRADES = (1, 2)  # 1 = relevant, 2 = highly relevant


class DatasetError(ValueError):
    pass


@dataclass
class Relevant:
    chunk_id: str
    grade: int
    version: str
    control_id: str | None
    source_file: str
    page: int
    section: str
    source_excerpt: str  # first characters of the chunk text, for auditing
    why: str


@dataclass
class Query:
    query_id: str
    question: str
    category: str
    difficulty: str
    version_filter: str | None
    status: str
    label_provenance: str
    human_reviewed: bool
    relevant: list[Relevant]
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def relevance(self) -> dict[str, int]:
        return {r.chunk_id: r.grade for r in self.relevant}

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in ("query_id", "question", "category", "difficulty",
                                           "version_filter", "status", "label_provenance",
                                           "human_reviewed", "notes")}
        d["relevant"] = [r.__dict__ for r in self.relevant]
        return d


def parse_query(d: dict) -> Query:
    try:
        rel = [Relevant(**r) for r in d["relevant"]]
        return Query(query_id=d["query_id"], question=d["question"], category=d["category"],
                     difficulty=d["difficulty"], version_filter=d["version_filter"],
                     status=d["status"], label_provenance=d["label_provenance"],
                     human_reviewed=d["human_reviewed"], relevant=rel, notes=d.get("notes", ""))
    except (KeyError, TypeError) as exc:
        raise DatasetError(f"malformed query record ({type(exc).__name__}: {exc})") from exc


def load_questions(path: Path) -> list[Query]:
    if not path.is_file():
        raise DatasetError(f"questions file not found: {path}")
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            out.append(parse_query(json.loads(line)))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"line {n}: invalid JSON ({exc})") from exc
    if not out:
        raise DatasetError("no questions found")
    return out


def validate_schema(queries: list[Query]) -> list[str]:
    errors = []
    seen = set()
    for q in queries:
        p = q.query_id
        if p in seen:
            errors.append(f"{p}: duplicate query_id")
        seen.add(p)
        if not q.question.strip():
            errors.append(f"{p}: empty question")
        if q.category not in CATEGORIES:
            errors.append(f"{p}: unknown category {q.category!r}")
        if q.difficulty not in DIFFICULTIES:
            errors.append(f"{p}: unknown difficulty {q.difficulty!r}")
        if q.status not in STATUSES:
            errors.append(f"{p}: unknown status {q.status!r}")
        if q.version_filter not in (None, "1.1", "2.0"):
            errors.append(f"{p}: bad version_filter {q.version_filter!r}")
        if q.label_provenance != PROVENANCE and not q.human_reviewed:
            errors.append(f"{p}: unrecognised label provenance {q.label_provenance!r}")
        if q.human_reviewed and q.label_provenance == PROVENANCE:
            errors.append(f"{p}: marked human_reviewed but provenance says AI-curated only")
        if not q.relevant:
            errors.append(f"{p}: no relevant chunks")
        ids = [r.chunk_id for r in q.relevant]
        if len(ids) != len(set(ids)):
            errors.append(f"{p}: repeated relevant chunk id")
        for r in q.relevant:
            if r.grade not in GRADES:
                errors.append(f"{p}/{r.chunk_id}: grade must be 1 or 2")
            if not r.why.strip():
                errors.append(f"{p}/{r.chunk_id}: missing relevance explanation")
            if q.version_filter and r.version != q.version_filter:
                errors.append(f"{p}/{r.chunk_id}: relevant chunk is outside the version filter")
        if q.status == "final" and not any(r.grade == 2 for r in q.relevant):
            errors.append(f"{p}: a final query needs at least one grade-2 chunk")
    return errors


def validate_against_db(queries: list[Query], db_path: Path) -> list[str]:
    """Every labelled chunk must exist and its provenance/excerpt must match the database."""
    conn = connect(db_path, readonly=True)
    errors = []
    try:
        for q in queries:
            for r in q.relevant:
                row = conn.execute(
                    "SELECT c.version, c.source_file, c.page, c.section, c.text, e.original_id "
                    "FROM chunk c LEFT JOIN element e ON e.version=c.version AND "
                    "e.element_id=c.element_id WHERE c.chunk_id=?", (r.chunk_id,)).fetchone()
                tag = f"{q.query_id}/{r.chunk_id}"
                if row is None:
                    errors.append(f"{tag}: chunk does not exist")
                    continue
                for name, stored, claimed in (("version", row["version"], r.version),
                                              ("source_file", row["source_file"], r.source_file),
                                              ("page", row["page"], r.page),
                                              ("section", row["section"], r.section),
                                              ("control_id", row["original_id"], r.control_id)):
                    if stored != claimed:
                        errors.append(f"{tag}: {name} is {claimed!r}, database has {stored!r}")
                if not r.source_excerpt or not row["text"].startswith(r.source_excerpt):
                    errors.append(f"{tag}: source_excerpt is not the start of the stored text")
    finally:
        conn.close()
    return errors


def validate(queries: list[Query], db_path: Path | None = None) -> list[str]:
    errors = validate_schema(queries)
    if db_path is not None:
        errors += validate_against_db(queries, db_path)
    return errors
