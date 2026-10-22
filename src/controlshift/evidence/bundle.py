from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .citations import CitationClaim


@dataclass
class EvidenceBundle:
    question: str
    query_type: str
    plan: dict
    referenced_versions: list[str]  # versions named in the question
    searched_versions: list[str]  # versions evidence was gathered from
    control_ids: list[str]  # normalized IDs referenced in the question
    control_records: list[dict] = field(default_factory=list)  # exact records from SQLite
    crosswalk_records: list[dict] = field(default_factory=list)  # official rows, verbatim
    passages: list[dict] = field(default_factory=list)  # retrieved chunks
    citations: dict[str, dict] = field(default_factory=dict)  # citation_id -> stored provenance
    conflicts: list[dict] = field(default_factory=list)
    unmapped_controls: list[dict] = field(default_factory=list)
    missing_evidence: list[dict] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    retrieval: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def claims(self) -> list[CitationClaim]:
        """The provenance this bundle asserts for each of its own citations."""
        out = []
        for cid, c in self.citations.items():
            if c["kind"] == "chunk":
                out.append(CitationClaim(cid, version=c["version"], source_file=c["source_file"],
                                         page=c["page"], section=c["section"],
                                         control_id=c.get("control_id")))
            else:
                out.append(CitationClaim(cid, focal_id=c["focal_id"], reference_id=c["reference_id"],
                                         check_reference=True, source_file=c["source_file"]))
        return out
