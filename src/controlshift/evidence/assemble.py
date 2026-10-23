"""Evidence assembly: exact control records + official crosswalk rows + retrieved passages.

Official mappings come only from the stored crosswalk rows. Similarity search supplies passages,
never mappings.
"""
from __future__ import annotations

from collections.abc import Callable

from ..ingest.models import normalize_control_id
from ..retrieval.hits import Hit
from ..store.queries import KnowledgeStore, NotFoundError
from .bundle import EvidenceBundle
from .citations import CitationClaim, chunk_citation_id, validate_citations, xwalk_citation_id
from .planner import (
    CONTROL_MAPPING,
    CROSS_VERSION,
    SINGLE_VERSION,
    UNSUPPORTED,
    QueryPlan,
    plan_query,
)

Retriever = Callable[[str, int, "str | None"], "list[Hit]"]

NEW_REASON = ("The official crosswalk marks this CSF 2.0 element as conceptually new "
              "(no CSF 1.1 reference element).")
NO_REF_REASON = ("No crosswalk row references this CSF 1.1 element. The workbook does not say "
                 "why, so this is not evidence that it was removed.")


class EvidenceAssembler:
    def __init__(self, store: KnowledgeStore, retriever: Retriever | None = None,
                 retrieval_label: str = "none", k: int = 5, mentions_per_control: int = 2,
                 max_retrieved_controls: int = 3, expand_min_hits: int = 2,
                 max_expanded_categories: int = 2, max_siblings: int = 12):
        self.store, self.retriever, self.label = store, retriever, retrieval_label
        self.k, self.mentions, self.max_ctrl = k, mentions_per_control, max_retrieved_controls
        # category expansion (broad cross-version comparisons only); see _expand_categories
        self.expand_min_hits, self.max_expanded, self.max_siblings = expand_min_hits, max_expanded_categories, max_siblings
        self._hits: dict[str, list[Hit]] = {}
        self.versions = [r[0] for r in store.conn.execute(
            "SELECT version FROM framework_version ORDER BY version")]

    # ---- public ---------------------------------------------------------------------------
    def assemble(self, question: str) -> EvidenceBundle:
        plan = plan_query(question)
        b = EvidenceBundle(
            question=question, query_type=plan.query_type, plan=plan.to_dict(),
            referenced_versions=list(plan.explicit_versions),
            searched_versions=[], control_ids=[c.normalized for c in plan.controls],
            unresolved_questions=list(plan.uncertainties),
            retrieval={"mode": self.label, "k_per_version": self.k, "hits": {}})
        if plan.query_type == UNSUPPORTED:
            return b
        self._hits = {}
        self._controls_and_mappings(plan, b)
        self._passages(plan, b)
        if plan.query_type == CROSS_VERSION:
            self._expand_categories(b)
        self._cue_extras(plan, b)
        return b

    # ---- registry helpers ---------------------------------------------------------------
    def _register_chunk(self, b: EvidenceBundle, c: dict) -> str:
        cid = chunk_citation_id(c["chunk_id"])
        b.citations[cid] = {"kind": "chunk", "chunk_id": c["chunk_id"], "version": c["version"],
                            "source_file": c["source_file"], "page": c["page"],
                            "printed_page": c.get("printed_page"), "section": c["section"],
                            "control_id": c.get("control_id")}
        return cid

    def _add_control(self, b: EvidenceBundle, element_id: str, version: str) -> bool:
        if any(r["version"] == version and r["element_id"] == _norm(element_id)
               for r in b.control_records):
            return True
        rec = self.store.get_control(element_id, version)
        if rec is None:
            return False
        own = self.store.get_evidence(rec["element_id"], version)[0]  # the control's own chunk
        chunk = {**own, "control_id": rec["original_id"]}
        b.control_records.append({
            "citation_id": self._register_chunk(b, chunk), "chunk_id": own["chunk_id"],
            "version": version, "control_id": rec["original_id"], "element_id": rec["element_id"],
            "level": rec["level"], "name": rec["name"], "description": rec["description"],
            "informative_reference_count": len(rec["informative_references"]),
            "source_file": own["source_file"], "page": own["page"],
            "printed_page": own["printed_page"], "section": own["section"], "text": own["text"]})
        return True

    def _add_xwalk(self, b: EvidenceBundle, row: dict, via: str) -> str:
        cid = xwalk_citation_id(row["excel_row"])
        existing = next((r for r in b.crosswalk_records if r["citation_id"] == cid), None)
        if existing:
            if via not in existing["via"]:
                existing["via"].append(via)
            return cid
        b.crosswalk_records.append({
            "citation_id": cid, "excel_row": row["excel_row"], "sheet": row["sheet"],
            "source_file": row["source_file"], "direction": "CSF 2.0 (focal) -> CSF 1.1 (reference)",
            "focal_version": row["focal_version"], "focal_id": row["focal_original_id"],
            "focal_description": row["focal_description"],
            "reference_version": row["reference_version"], "reference_id": row["reference_original_id"],
            "reference_description": row["reference_description"], "mapping_type": row["mapping_type"],
            "comments": row["comments"], "strength": row["strength"], "via": [via]})
        b.citations[cid] = {"kind": "crosswalk", "excel_row": row["excel_row"],
                            "focal_id": row["focal_original_id"],
                            "reference_id": row["reference_original_id"],
                            "source_file": row["source_file"]}
        return cid

    # ---- controls and official mappings ---------------------------------------------------
    def _controls_and_mappings(self, plan: QueryPlan, b: EvidenceBundle) -> None:
        # In a mapping question a named version may be the source OR the target of the mapping,
        # so controls are looked up in every version; only single-version lookups are restricted.
        explicit = plan.explicit_versions if plan.query_type == SINGLE_VERSION else []
        check = explicit or self.versions
        found_in: dict[str, list[str]] = {}
        for ref in plan.controls:
            found = [v for v in check if self._add_control(b, ref.normalized, v)]
            found_in[ref.normalized] = found
            if not found or explicit:
                missing_in = [v for v in check if v not in found]
                if missing_in:
                    b.missing_evidence.append({"kind": "control_not_found", "control_id": ref.raw,
                                               "versions_checked": missing_in})
                if explicit and missing_in:
                    other = [x for x in self.versions if x not in explicit
                             and self.store.get_control(ref.normalized, x)]
                    if other:
                        b.unresolved_questions.append(
                            f"{ref.raw} does not exist in CSF {', '.join(missing_in)} (named in the "
                            f"question) but exists in CSF {', '.join(other)}; no mapping was assumed.")
            elif len(found) > 1 and plan.query_type == CONTROL_MAPPING and plan.explicit_versions:
                b.unresolved_questions.append(
                    f"{ref.raw} exists in both CSF versions; the named version "
                    f"({', '.join(plan.explicit_versions)}) could be the source or the target of "
                    "the mapping, so mappings are reported in both directions.")
            elif len(found) > 1 and plan.query_type == SINGLE_VERSION:
                b.unresolved_questions.append(
                    f"{ref.raw} exists in both CSF versions and the question names none; "
                    "records for both are reported.")
        if plan.query_type == CONTROL_MAPPING:
            for ref in plan.controls:
                for v in found_in[ref.normalized]:
                    self._attach_mappings(b, ref.normalized, v, f"question:{ref.raw}@{v}")
        b.control_ids = [c.normalized for c in plan.controls]
        self._found_in = found_in

    def _attach_mappings(self, b: EvidenceBundle, element_id: str, version: str, via: str, ground: bool = True) -> None:
        """Add the official crosswalk rows touching one element and classify them. `ground` also adds a control record for
        each counterpart (the crosswalk row itself already quotes both descriptions)."""
        try:
            rows = (self.store.mappings_2_0_to_1_1(element_id) if version == "2.0"
                    else self.store.mappings_1_1_to_2_0(element_id))
        except NotFoundError:
            return
        cites = [self._add_xwalk(b, r, via) for r in rows]
        for r in rows if ground else []:  # ground each counterpart with its own control record
            if r["reference_element_id"] and version == "2.0":
                self._add_control(b, r["reference_element_id"], "1.1")
            if version == "1.1":
                self._add_control(b, r["focal_element_id"], "2.0")
        label = _display(b, element_id, version)
        if version == "2.0":
            kinds = {r["mapping_type"] for r in rows}
            if kinds == {"new_in_2_0"}:
                _once(b.unmapped_controls, {"control_id": label, "version": version,
                                            "reason": NEW_REASON, "citations": cites})
            elif {"mapped", "new_in_2_0"} <= kinds:  # e.g. GV.SC-03: both kinds of record
                _once(b.conflicts, {
                    "kind": "mapped_and_new_in_2_0", "control_id": label, "version": version,
                    "citations": cites,
                    "note": "The official workbook holds both mapped row(s) and a 'conceptually "
                            "new' row for this element. Both are reported; neither is preferred."})
        elif not rows:
            _once(b.unmapped_controls, {"control_id": label, "version": version,
                                        "reason": NO_REF_REASON, "citations": []})

    # ---- passages ------------------------------------------------------------------------------
    def _passages(self, plan: QueryPlan, b: EvidenceBundle) -> None:
        if plan.explicit_versions and plan.query_type == SINGLE_VERSION:
            versions = plan.explicit_versions
        elif plan.query_type == SINGLE_VERSION and plan.controls:
            seen = {v for vs in self._found_in.values() for v in vs}
            versions = [v for v in self.versions if v in seen] or self.versions
        else:
            versions = self.versions
        b.searched_versions = list(versions)
        k = 3 if plan.query_type == CONTROL_MAPPING else self.k
        b.retrieval["k_per_version"] = k
        for rec in list(b.control_records):  # narrative that mentions a retrieved control
            if rec["version"] in versions:
                self._add_mentions(b, rec)
        if self.retriever is None:
            b.retrieval["mode"] = "none"
            return
        for v in versions:
            hits = self.retriever(plan.question, k, v)
            b.retrieval["hits"][v] = len(hits)
            self._hits[v] = hits
            if not hits:
                b.missing_evidence.append({"kind": "no_passages", "version": v,
                                           "detail": "retrieval returned nothing for this version"})
            for h in hits:
                self._add_passage(b, h.to_dict(), f"retrieval:{self.label}")
            if plan.query_type == CROSS_VERSION:  # official links for the top retrieved controls
                for h in [h for h in hits if h.chunk_type != "text"][: self.max_ctrl]:
                    self._add_control(b, h.control_id, v)
                    self._attach_mappings(b, h.control_id, v, f"retrieved:{h.control_id}@{v}")

    # ---- category expansion (broad comparisons) -----------------------------------------------
    def _level(self, control_id: str, version: str) -> str | None:
        rec = self.store.get_control(control_id, version)
        return rec["level"] if rec else None

    def _category_of(self, control_id: str, version: str) -> str | None:
        rec = self.store.get_control(control_id, version)
        if rec is None or rec["level"] == "function":
            return None
        return rec["element_id"] if rec["level"] == "category" else rec["category_id"]

    def _expand_categories(self, b: EvidenceBundle) -> None:
        """A broad comparison ("differences ... for <topic>") is about whole categories, but top-k similarity search returns
        scattered pieces of them. When at least `expand_min_hits` retrieved hits of one version fall in the same category,
        add that category's record, ALL its subcategory records, and the official crosswalk rows for the category and its
        subcategories (the bundle stays complete; the context builder decides what fits the generator's budget); the category the crosswalk pairs it with in the other version is expanded the same way. Everything
        comes from the store (official records only) and keeps its own version, provenance and citation id. Narrow
        questions (exact control, mapping) never reach this path."""
        counts: dict[tuple[str, str], int] = {}
        for v, hits in self._hits.items():
            for h in hits:
                if h.chunk_type != "text" and h.control_id:
                    cat = self._category_of(h.control_id, v)
                    if cat:
                        counts[(v, cat)] = counts.get((v, cat), 0) + 1
        chosen = sorted((kv for kv in counts.items() if kv[1] >= self.expand_min_hits), key=lambda kv: (-kv[1], kv[0]))
        todo = [key for key, _ in chosen[: self.max_expanded]]
        done: set[tuple[str, str]] = set()
        while todo:
            v, cat = todo.pop(0)
            if (v, cat) in done:
                continue
            done.add((v, cat))
            if not self._add_control(b, cat, v):
                continue
            via = f"category_expansion:{cat}@{v}"
            self._attach_mappings(b, cat, v, via, ground=False)  # the category-level official row(s)
            for sub in self.store.list_controls_in_category(cat, v)[: self.max_siblings]:
                self._add_control(b, sub["element_id"], v)  # canonical definition of every subcategory
                self._attach_mappings(b, sub["element_id"], v, via, ground=False)  # and its official rows
            for r in b.crosswalk_records:  # the category paired with this one in the other version
                pair = ("1.1", r["reference_id"]) if v == "2.0" and r["focal_id"] == cat else (
                    ("2.0", r["focal_id"]) if v == "1.1" and r["reference_id"] == cat else None)
                if pair and pair[1] and self._category_of(pair[1], pair[0]) == pair[1] and pair not in done:
                    todo.append(pair)
        if done:
            b.retrieval["expanded_categories"] = sorted(f"{c}@{v}" for v, c in done)

    def _add_mentions(self, b: EvidenceBundle, rec: dict) -> None:
        extra = [e for e in self.store.get_evidence(rec["element_id"], rec["version"])
                 if e["relation"] == "mention"][: self.mentions]
        for e in extra:
            self._add_passage(b, {**e, "rank": None, "score": None, "mode": "mention"},
                              "control_mention")

    def _add_passage(self, b: EvidenceBundle, d: dict, origin: str) -> None:
        cid = chunk_citation_id(d["chunk_id"])
        if cid in b.citations:  # already present as a control record or earlier passage
            return
        self._register_chunk(b, d)
        b.passages.append({
            "citation_id": cid, "origin": origin, "rank": d.get("rank"), "score": d.get("score"),
            "mode": d.get("mode"), "chunk_id": d["chunk_id"], "version": d["version"],
            "control_id": d.get("control_id"), "chunk_type": d["chunk_type"],
            "source_file": d["source_file"], "page": d["page"],
            "printed_page": d.get("printed_page"), "section": d["section"], "text": d["text"]})

    # ---- cue-driven official records ---------------------------------------------------------
    def _cue_extras(self, plan: QueryPlan, b: EvidenceBundle) -> None:
        if plan.query_type == CROSS_VERSION and "change:new" in plan.cues:
            rows = self.store.conn.execute(
                "SELECT * FROM crosswalk_mapping WHERE mapping_type='new_in_2_0' ORDER BY excel_row")
            for r in rows:
                self._add_xwalk(b, dict(r), "cue:new")


def _norm(x: str) -> str:
    return normalize_control_id(x)


def _display(b: EvidenceBundle, element_id: str, version: str) -> str:
    for r in b.control_records:
        if r["version"] == version and r["element_id"] == _norm(element_id):
            return r["control_id"]
    return element_id


def _once(items: list[dict], item: dict) -> None:
    if item not in items:
        items.append(item)


def validate_bundle(store: KnowledgeStore, b: EvidenceBundle) -> dict:
    """Structural validation of every citation the bundle makes, plus agreement between each
    evidence entry and the registry it cites. Says nothing about semantic faithfulness."""
    checks = validate_citations(store.conn, b.claims())
    errors = {c.citation_id: c.errors for c in checks if not c.valid}
    for rec in b.control_records + b.passages:
        reg = b.citations.get(rec["citation_id"])
        stored = store.conn.execute("SELECT text FROM chunk WHERE chunk_id=?",
                                    (rec["chunk_id"],)).fetchone()
        if reg is None:
            errors.setdefault(rec["citation_id"], []).append("entry has no registered citation")
        elif stored is None or stored["text"] != rec["text"]:
            errors.setdefault(rec["citation_id"], []).append("quoted text differs from stored chunk")
        elif any(rec[f] != reg[f] for f in ("version", "page", "section", "source_file")):
            errors.setdefault(rec["citation_id"], []).append("entry provenance differs from citation")
    for rec in b.crosswalk_records:
        if rec["citation_id"] not in b.citations:
            errors.setdefault(rec["citation_id"], []).append("entry has no registered citation")
    return {"scope": "structural (existence + provenance); semantic faithfulness is not checked",
            "citations_checked": len(checks), "invalid": len(errors), "errors": errors}


__all__ = ["CitationClaim", "EvidenceAssembler", "Retriever", "validate_bundle"]
