"""Phase 5B step 2: grounded-answer evaluation (offline-first).

Three kinds of assurance are kept strictly apart:
  * structural      - cited ids exist / belong to the evidence bundle (no claim about meaning);
  * deterministic   - rule checks against SQLite records and the gold file (mappings, versions,
                      conflicts, abstention, removal wording);
  * semantic        - whether prose is faithful to the cited text: ALWAYS left to a human reviewer.
Nothing here measures a language model unless a live provider is explicitly supplied.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from ..evidence.assemble import validate_bundle
from ..evidence.citations import CitationClaim, validate_citations, xwalk_citation_id
from ..generation.generate import REMOVAL_WORDS, insufficient_evidence
from ..generation.schema import LLMAnswer
from ..ingest.models import normalize_control_id
from ..store.schema import connect

CATEGORIES = ["exact_control", "comparison", "official_mapping", "one_to_many",
              "conceptually_new", "conflict", "missing_mapping", "abstention", "invalid_input"]
# Evidence-based abstention (the question is valid but the evidence cannot support an answer) is
# different from invalid input (rejected by the API with HTTP 422 before any retrieval/generation).
ABSTENTION_BASES = ("control_not_found", "topic_absent", "evidence_absent")
PROVENANCE = "ai_curated_source_checked"
SEMANTIC = "requires_human_review"
GROUNDEDNESS = ["grounded", "partially_grounded", "not_grounded"]
COMPLETENESS = ["complete", "partial", "incomplete"]


class GoldError(ValueError):
    pass


# ================================================================== gold dataset
def load_gold(path: Path) -> list[dict]:
    if not path.is_file():
        raise GoldError(f"gold file not found: {path}")
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise GoldError(f"line {n}: invalid JSON ({exc})") from exc
    if not out:
        raise GoldError("gold file is empty")
    return out


REQUIRED = ["question_id", "category", "question", "expected_query_type", "expected_controls",
            "expected_crosswalk_rows", "expected_mappings", "conflict_rows", "expect_new",
            "forbidden_mapping_controls", "allowed_versions", "must_abstain", "abstention_basis",
            "absent_terms", "expected_facts", "abstention_conditions", "row_coverage", "review"]


def validate_gold_schema(gold: list[dict]) -> list[str]:
    errors, seen = [], set()
    for g in gold:
        q = g.get("question_id", "?")
        missing = [k for k in REQUIRED if k not in g]
        if missing:
            errors.append(f"{q}: missing fields {missing}")
            continue
        if q in seen:
            errors.append(f"{q}: duplicate question_id")
        seen.add(q)
        if g["category"] not in CATEGORIES:
            errors.append(f"{q}: unknown category {g['category']!r}")
        if g["review"].get("human_reviewed") is not False or g["review"].get(
                "label_provenance") != PROVENANCE:
            errors.append(f"{q}: review block must state AI-curated and not human-reviewed")
        if g["must_abstain"] and not g["abstention_basis"]:
            errors.append(f"{q}: must_abstain needs an abstention_basis")
        invalid = g.get("invalid_input", False)
        if invalid:
            if g["category"] != "invalid_input" or g["must_abstain"] or g["abstention_basis"] \
                    or g.get("expected_api_status") != 422 or g["expected_query_type"] != "unsupported":
                errors.append(f"{q}: invalid input must be category invalid_input, expect HTTP 422, "
                              "and is not an evidence-based abstention")
        elif g["category"] == "invalid_input":
            errors.append(f"{q}: category invalid_input requires invalid_input=true")
        if g["category"] == "abstention" and (not g["must_abstain"]
                                              or g["abstention_basis"] not in ABSTENTION_BASES):
            errors.append(f"{q}: an abstention question needs must_abstain and a basis in {ABSTENTION_BASES}")
        if g["abstention_basis"] == "topic_absent" and (
                len(set(g["absent_terms"])) < 3 or not g.get("abstention_justification", "").strip()):
            errors.append(f"{q}: topic_absent needs >=3 absent concept terms (not one keyword) "
                          "and a written justification")
        if g["must_abstain"] and (g["expected_mappings"] or g["expected_crosswalk_rows"]):
            errors.append(f"{q}: an abstention question must not expect mappings")
        if not g["must_abstain"] and not invalid and not (
                g["expected_facts"] or g["expected_mappings"] or g["expected_controls"]):
            errors.append(f"{q}: answerable question has no expected facts/mappings/controls")
        if g["row_coverage"] not in ("all", "any"):
            errors.append(f"{q}: row_coverage must be 'all' or 'any'")
        for f in g["expected_facts"]:
            if f.get("type") not in ("text", "mapping") or not f.get("statement"):
                errors.append(f"{q}: malformed expected fact {f}")
    return errors


def _norm_ws(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def validate_gold_against_db(gold: list[dict], db: Path) -> list[str]:
    """Every expectation must be true of the stored documents / official crosswalk rows."""
    conn = connect(db, readonly=True)
    errors = []
    try:
        for g in gold:
            q = g["question_id"]
            for c in g["expected_controls"]:
                if not conn.execute("SELECT 1 FROM element WHERE version=? AND element_id=?",
                                    (c["version"], normalize_control_id(c["control_id"]))).fetchone():
                    errors.append(f"{q}: control {c['control_id']} not in CSF {c['version']}")
            for row in g["expected_crosswalk_rows"]:
                if not conn.execute("SELECT 1 FROM crosswalk_mapping WHERE excel_row=?",
                                    (row,)).fetchone():
                    errors.append(f"{q}: crosswalk row {row} does not exist")
            for m in g["expected_mappings"]:
                r = conn.execute("SELECT focal_original_id, reference_original_id FROM "
                                 "crosswalk_mapping WHERE excel_row=?", (m["row"],)).fetchone()
                if not r or (r[0], r[1]) != (m["focal"], m["reference"]):
                    errors.append(f"{q}: mapping {m} does not match crosswalk row {m['row']}")
                if m["row"] not in g["expected_crosswalk_rows"]:
                    errors.append(f"{q}: mapping row {m['row']} missing from expected_crosswalk_rows")
            for row in g["conflict_rows"]:
                if row not in g["expected_crosswalk_rows"]:
                    errors.append(f"{q}: conflict row {row} not in expected rows")
            if g["conflict_rows"]:
                kinds = {r[0] for r in conn.execute(
                    f"SELECT mapping_type FROM crosswalk_mapping WHERE excel_row IN "
                    f"({','.join('?' * len(g['conflict_rows']))})", g["conflict_rows"])}
                if kinds != {"mapped", "new_in_2_0"}:
                    errors.append(f"{q}: conflict rows are not a mapped+new pair ({kinds})")
            for focal in g["expect_new"]:
                kinds = {r[0] for r in conn.execute(
                    "SELECT mapping_type FROM crosswalk_mapping WHERE focal_original_id=?", (focal,))}
                if kinds != {"new_in_2_0"}:
                    errors.append(f"{q}: {focal} is not purely 'conceptually new' ({kinds})")
            for ctl in g["forbidden_mapping_controls"]:
                n = conn.execute("SELECT COUNT(*) FROM crosswalk_mapping WHERE reference_original_id=?"
                                 " OR focal_original_id=?", (ctl, ctl)).fetchone()[0]
                if n:
                    errors.append(f"{q}: {ctl} has {n} crosswalk rows but is expected unmapped")
            for term in g["absent_terms"]:
                n = conn.execute("SELECT COUNT(*) FROM chunk WHERE lower(text) LIKE ?",
                                 (f"%{term.lower()}%",)).fetchone()[0]
                if n:
                    errors.append(f"{q}: term {term!r} occurs in {n} chunks, not absent")
            for term, info in g.get("reviewed_related_terms", {}).items():
                n = conn.execute("SELECT COUNT(*) FROM chunk WHERE lower(text) LIKE ?",
                                 (f"%{term.lower()}%",)).fetchone()[0]
                if n != info["chunks"] or not info.get("note", "").strip():
                    errors.append(f"{q}: related term {term!r} occurs in {n} chunks, gold says "
                                  f"{info['chunks']} (or the review note is missing)")
            for f in g["expected_facts"]:
                ev = f.get("evidence", "")
                if f["type"] == "text":
                    cid = ev.removeprefix("chunk:")
                    row = conn.execute("SELECT text FROM chunk WHERE chunk_id=?", (cid,)).fetchone()
                    if row is None:
                        errors.append(f"{q}: fact evidence chunk {cid} does not exist")
                    elif _norm_ws(f["quote"]) not in _norm_ws(row[0]):
                        errors.append(f"{q}: fact quote is not in stored text of {cid}")
                else:
                    if ev != xwalk_citation_id(f["row"]) or f["row"] not in g["expected_crosswalk_rows"]:
                        errors.append(f"{q}: mapping fact evidence/row inconsistent: {f}")
    finally:
        conn.close()
    return errors


# ================================================================== check results
def result(name: str, level: str, status: str, detail: str = "") -> dict:
    assert status in ("pass", "fail", "n/a")
    return {"name": name, "level": level, "status": status, "detail": detail}


def _cited(a: LLMAnswer) -> list[str]:
    ids = list(a.citations)
    for k in a.key_changes:
        ids += k.citations
    for m in a.mappings:
        ids += m.citations
    return list(dict.fromkeys(ids))


def _rows_in(ids: list[str]) -> set[int]:
    return {int(i.removeprefix("xwalk:row")) for i in ids if i.startswith("xwalk:row")
            and i.removeprefix("xwalk:row").isdigit()}


def _pair(focal: str, ref: str | None) -> tuple[str, str | None]:
    return (normalize_control_id(focal.upper()), normalize_control_id(ref.upper()) if ref else None)


# ================================================================== answer checks
def check_answer(raw: object, gold: dict, conn: sqlite3.Connection,
                 allowed: set[str] | None) -> list[dict]:
    """Deterministic checks of one answer (a dict as returned by the generator) against the gold
    expectations and SQLite. `allowed` = citation ids of the evidence bundle shown to the model.
    Semantic faithfulness is never decided here."""
    S, F = "structural", "deterministic_factual"
    if gold.get("invalid_input"):
        return [result("not_applicable", S, "n/a", "request is rejected with HTTP 422 before generation")]
    try:
        a = LLMAnswer.model_validate(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        return [result("schema_valid", S, "fail", re.sub(r"\s+", " ", str(exc))[:160])]
    out = [result("schema_valid", S, "pass")]
    cited = _cited(a)

    bad = [c for c in cited if not validate_citations(conn, [CitationClaim(c)])[0].valid]
    out.append(result("citation_ids_valid", S, "fail" if bad else "pass",
                      f"nonexistent/malformed: {bad}" if bad else ""))
    if allowed is None:
        out.append(result("citations_in_bundle", S, "n/a"))
    else:
        outside = [c for c in cited if c not in allowed]
        out.append(result("citations_in_bundle", S, "fail" if outside else "pass",
                          f"not in evidence bundle: {outside}" if outside else ""))

    # abstention
    if gold["must_abstain"] != a.abstained:
        out.append(result("abstention_correct", F, "fail",
                          "should abstain" if gold["must_abstain"] else "abstained although evidence supports an answer"))
    else:
        out.append(result("abstention_correct", F, "pass"))
    if a.abstained:
        for name in ("mapping_pairs_official", "mapping_cites_matching_row", "versions_correct",
                     "expected_rows_covered", "expected_controls_referenced", "conflict_preserved",
                     "new_control_no_reference", "no_forbidden_mappings", "no_unsupported_removal",
                     "no_uncited_claims"):
            out.append(result(name, F, "n/a", "answer abstained"))
        return out

    # mappings
    official = {(r[0], r[1], r[2]) for r in conn.execute(
        "SELECT focal_element_id, reference_element_id, excel_row FROM crosswalk_mapping")}
    pairs = {(f, r) for f, r, _ in official}
    invented = [(m.focal_id, m.reference_id) for m in a.mappings
                if _pair(m.focal_id, m.reference_id) not in pairs]
    out.append(result("mapping_pairs_official", F, "fail" if invented else "pass",
                      f"not in the official crosswalk: {invented}" if invented else ""))
    miscited = []
    for m in a.mappings:
        rows = _rows_in(m.citations)
        if not any((_pair(m.focal_id, m.reference_id)[0], _pair(m.focal_id, m.reference_id)[1], r)
                   in official for r in rows):
            miscited.append((m.focal_id, m.reference_id))
    out.append(result("mapping_cites_matching_row", F, "fail" if miscited else "pass",
                      f"citation does not carry this pair: {miscited}" if miscited else ""))

    # versions
    allowed_v = set(gold["allowed_versions"])
    wrong = []
    for c in cited:
        if c.startswith("chunk:"):
            row = conn.execute("SELECT version FROM chunk WHERE chunk_id=?", (c[6:],)).fetchone()
            if row and row[0] not in allowed_v:
                wrong.append(f"{c} is CSF {row[0]}")
    for m in a.mappings:
        f, r = _pair(m.focal_id, m.reference_id)
        if not conn.execute("SELECT 1 FROM element WHERE version='2.0' AND element_id=?", (f,)).fetchone():
            wrong.append(f"mapping focal {m.focal_id} is not a CSF 2.0 control")
        if r and not conn.execute("SELECT 1 FROM element WHERE version='1.1' AND element_id=?", (r,)).fetchone():
            wrong.append(f"mapping reference {m.reference_id} is not a CSF 1.1 control")
    out.append(result("versions_correct", F, "fail" if wrong else "pass", "; ".join(wrong)))

    # expected rows / controls
    cited_rows = _rows_in(cited)
    expected_rows = set(gold["expected_crosswalk_rows"])
    if not expected_rows:
        out.append(result("expected_rows_covered", F, "n/a"))
    else:
        missing = sorted(expected_rows - cited_rows)
        need_all = gold["row_coverage"] == "all"
        failed = bool(missing) if need_all else not (expected_rows & cited_rows)
        out.append(result("expected_rows_covered", F, "fail" if failed else "pass",
                          f"official rows not cited: {missing}" if failed else ""))
    if not gold["expected_controls"]:
        out.append(result("expected_controls_referenced", F, "n/a"))
    else:
        text = " ".join([a.answer, *[k.statement for k in a.key_changes]]).upper()
        mentioned = set()
        for c in cited:
            if c.startswith("chunk:"):
                mentioned.add(c[6:])
        miss = []
        for c in gold["expected_controls"]:
            norm = normalize_control_id(c["control_id"])
            cid_hit = any(m.startswith(f"csf{c['version']}:") and m.endswith(":" + c["control_id"])
                          for m in mentioned) or any(
                m.startswith(f"csf{c['version']}:") and normalize_control_id(m.rsplit(":", 1)[1]) == norm
                for m in mentioned)
            text_hit = re.search(rf"\b{re.escape(c['control_id'].upper())}\b", text) is not None
            if not (cid_hit or text_hit):
                miss.append(f"{c['control_id']} (CSF {c['version']})")
        out.append(result("expected_controls_referenced", F, "fail" if miss else "pass",
                          f"not referenced: {miss}" if miss else ""))

    # conflicts
    if not gold["conflict_rows"]:
        out.append(result("conflict_preserved", F, "n/a"))
    else:
        rows = set(gold["conflict_rows"])
        focals = {r[0] for r in conn.execute(
            f"SELECT focal_element_id FROM crosswalk_mapping WHERE excel_row IN "
            f"({','.join('?' * len(rows))})", list(rows))}
        has_ref = any(m.reference_id for m in a.mappings if _pair(m.focal_id, None)[0] in focals)
        has_none = any(not m.reference_id for m in a.mappings if _pair(m.focal_id, None)[0] in focals)
        problems = []
        if rows - cited_rows:
            problems.append(f"conflicting rows not all cited: {sorted(rows - cited_rows)}")
        if not (has_ref and has_none):
            problems.append("mappings must include both the mapped and the 'conceptually new' record")
        if not re.search(r"conflict|both|inconsistent|disagree|also", a.answer + " ".join(a.uncertainties),
                         re.IGNORECASE):
            problems.append("answer text does not flag the disagreement")
        out.append(result("conflict_preserved", F, "fail" if problems else "pass", "; ".join(problems)))
    if not gold["expect_new"]:
        out.append(result("new_control_no_reference", F, "n/a"))
    else:
        bad_new = [m.focal_id for m in a.mappings
                   if _pair(m.focal_id, None)[0] in {normalize_control_id(x) for x in gold["expect_new"]}
                   and m.reference_id]
        out.append(result("new_control_no_reference", F, "fail" if bad_new else "pass",
                          f"reference given for conceptually new control: {bad_new}" if bad_new else ""))
    if not gold["forbidden_mapping_controls"]:
        out.append(result("no_forbidden_mappings", F, "n/a"))
    else:
        forb = {normalize_control_id(x) for x in gold["forbidden_mapping_controls"]}
        hit = [(m.focal_id, m.reference_id) for m in a.mappings
               if _pair(m.focal_id, m.reference_id)[0] in forb or _pair(m.focal_id, m.reference_id)[1] in forb]
        out.append(result("no_forbidden_mappings", F, "fail" if hit else "pass",
                          f"mapping claimed for an unmapped control: {hit}" if hit else ""))

    # removal wording
    texts = {}
    for c in cited:
        if c.startswith("chunk:"):
            row = conn.execute("SELECT text FROM chunk WHERE chunk_id=?", (c[6:],)).fetchone()
            texts[c] = row[0] if row else ""
        elif c.startswith("xwalk:row") and c[9:].isdigit():
            row = conn.execute("SELECT coalesce(focal_description,'')||' '||coalesce(reference_description,'')"
                               "||' '||coalesce(comments,'') FROM crosswalk_mapping WHERE excel_row=?",
                               (int(c[9:]),)).fetchone()
            texts[c] = row[0] if row else ""
    unsupported = []
    for stmt, cites in [(a.answer, a.citations), *[(k.statement, k.citations) for k in a.key_changes]]:
        for m in REMOVAL_WORDS.finditer(stmt):
            if not any(m.group(1).lower() in texts.get(c, "").lower() for c in cites):
                unsupported.append(m.group(1).lower())
                break
    out.append(result("no_unsupported_removal", F, "fail" if unsupported else "pass",
                      f"removal wording without support: {unsupported}" if unsupported else ""))
    uncited = []
    if not a.citations:
        uncited.append("answer has no citations")
    uncited += [f"key_change {i + 1}" for i, k in enumerate(a.key_changes) if not k.citations]
    uncited += [f"mapping {m.focal_id}->{m.reference_id}" for m in a.mappings if not m.citations]
    out.append(result("no_uncited_claims", F, "fail" if uncited else "pass", "; ".join(uncited)))
    return out


def summarize_checks(checks: list[dict]) -> dict:
    fails = [c["name"] for c in checks if c["status"] == "fail"]
    return {"all_passed": not fails, "failed_checks": fails,
            "n_applicable": sum(c["status"] != "n/a" for c in checks), "semantic_faithfulness": SEMANTIC}


# ================================================================== evidence-stage evaluation
def evidence_checks(bundle, gold: dict, store) -> list[dict]:
    """Deterministic checks of the evidence bundle the pipeline builds for a question (no LLM)."""
    P = "evidence_pipeline"
    out = [result("query_type", P, "pass" if bundle.query_type == gold["expected_query_type"] else "fail",
                  f"got {bundle.query_type}, expected {gold['expected_query_type']}"
                  if bundle.query_type != gold["expected_query_type"] else "")]
    have = {(r["version"], r["element_id"]) for r in bundle.control_records}
    miss = [f"{c['control_id']}@{c['version']}" for c in gold["expected_controls"]
            if (c["version"], normalize_control_id(c["control_id"])) not in have]
    out.append(result("expected_controls_present", P,
                      "n/a" if not gold["expected_controls"] else ("fail" if miss else "pass"),
                      f"missing control records: {miss}" if miss else ""))
    rows = {r["excel_row"] for r in bundle.crosswalk_records}
    exp = set(gold["expected_crosswalk_rows"])
    out.append(result("expected_rows_present", P, "n/a" if not exp else (
        "fail" if exp - rows else "pass"), f"official rows missing: {sorted(exp - rows)}" if exp - rows else ""))
    if gold["conflict_rows"]:
        shown = [c for c in bundle.conflicts if set(gold["conflict_rows"]) <=
                 {int(x.removeprefix("xwalk:row")) for x in c["citations"]}]
        out.append(result("conflict_surfaced", P, "pass" if shown else "fail",
                          "" if shown else "conflicting crosswalk rows were not flagged"))
    else:
        out.append(result("conflict_surfaced", P, "n/a"))
    flag_ids = {u["control_id"].upper() for u in bundle.unmapped_controls}
    want = [x for x in gold["expect_new"]] + list(gold["forbidden_mapping_controls"])
    out.append(result("unmapped_flagged", P, "n/a" if not want else (
        "pass" if all(w.upper() in flag_ids for w in want) else "fail"),
        f"flagged: {sorted(flag_ids)}" if want and not all(w.upper() in flag_ids for w in want) else ""))
    want_u = gold.get("expected_unresolved", [])
    joined = " ".join(bundle.unresolved_questions)
    absent = [w for w in want_u if w not in joined]
    out.append(result("expected_uncertainty_surfaced", P, "n/a" if not want_u else (
        "fail" if absent else "pass"), f"ambiguity not recorded: {absent}" if absent else ""))
    allowed_v = set(gold["allowed_versions"])
    leaked = sorted({p["version"] for p in bundle.passages} - allowed_v)
    out.append(result("version_isolation", P, "fail" if leaked else "pass",
                      f"passages from versions {leaked} outside {sorted(allowed_v)}" if leaked else ""))
    invalid = validate_bundle(store, bundle)
    out.append(result("bundle_citations_structurally_valid", P,
                      "fail" if invalid["invalid"] else "pass", json.dumps(invalid["errors"])[:200]))
    if gold["abstention_basis"] == "control_not_found":
        ok = any(m["kind"] == "control_not_found" for m in bundle.missing_evidence) and not (
            bundle.control_records or bundle.crosswalk_records)
        out.append(result("missing_evidence_reported", P, "pass" if ok else "fail",
                          "" if ok else "unknown control not reported / evidence invented"))
    elif gold.get("invalid_input"):
        from pydantic import ValidationError

        from ..api.schemas import AskRequest, CompareRequest
        rejected = []
        for model in (AskRequest, CompareRequest):
            try:
                model(question=gold["question"])
            except ValidationError:
                rejected.append(model.__name__)
        ok = len(rejected) == 2
        out.append(result("rejected_as_invalid_request", P, "pass" if ok else "fail",
                          "" if ok else "the API request model accepted this question (expected HTTP 422)"))
        reach = bundle.query_type == "unsupported" and insufficient_evidence(bundle) is not None
        out.append(result("defence_in_depth_if_reached", P, "pass" if reach else "fail",
                          "" if reach else "if it bypassed validation the pipeline would not abstain"))
    elif gold["abstention_basis"] == "evidence_absent":
        ok = insufficient_evidence(bundle) is not None
        out.append(result("deterministic_abstention", P, "pass" if ok else "fail",
                          "" if ok else "bundle holds evidence, so the generator would call the LLM"))
    else:
        out.append(result("missing_evidence_reported", P, "n/a"))
    return out


# ================================================================== validator self-test
def reference_fixture(gold: dict, conn: sqlite3.Connection) -> tuple[dict, set[str]] | None:
    """A synthetic answer built ONLY from the gold expectations (not a model output), plus the set
    of citation ids it is allowed to use. Used to check that the checker accepts good answers."""
    allowed: set[str] = set()
    if gold.get("invalid_input"):
        return None  # never reaches generation
    if gold["must_abstain"]:
        return ({"answer": "", "abstained": True,
                 "abstention_reason": gold["abstention_conditions"]}, allowed)
    citations: list[str] = []
    mappings, key_changes, parts = [], [], []
    for c in gold["expected_controls"]:
        row = conn.execute("SELECT chunk_id, text FROM chunk WHERE version=? AND element_id=?",
                           (c["version"], normalize_control_id(c["control_id"]))).fetchone()
        if row:
            cid = f"chunk:{row[0]}"
            allowed.add(cid)
            citations.append(cid)
            parts.append(f"{c['control_id']} (CSF {c['version']}): {_norm_ws(row[1])}")
    for f in gold["expected_facts"]:
        if f["type"] == "text":
            allowed.add(f["evidence"])
            citations.append(f["evidence"])
            parts.append(f["quote"])
    for m in gold["expected_mappings"]:
        cid = xwalk_citation_id(m["row"])
        allowed.add(cid)
        citations.append(cid)
        mappings.append({"focal_id": m["focal"], "reference_id": m["reference"],
                         "note": "official crosswalk row", "citations": [cid]})
        key_changes.append({"statement": f"Official row {m['row']}: {m['focal']} -> "
                            f"{m['reference'] or 'no CSF 1.1 reference'}.", "citations": [cid]})
    if gold["conflict_rows"]:
        parts.append("The official records conflict: both a mapped row and a conceptually new row exist.")
    if gold["forbidden_mapping_controls"]:
        parts.append("No official crosswalk row references this control; the workbook gives no reason.")
    if not citations:
        return None
    return ({"answer": " ".join(parts) or "See cited evidence.", "citations": list(dict.fromkeys(citations)),
             "key_changes": key_changes, "mappings": mappings, "uncertainties": [],
             "unresolved_questions": [], "abstained": False}, allowed)


def _first_other_chunk(conn, allowed: set[str], version: str | None = None) -> str:
    q = "SELECT chunk_id FROM chunk" + (" WHERE version=?" if version else "") + " ORDER BY ordinal"
    for (cid,) in conn.execute(q, (version,) if version else ()):
        if f"chunk:{cid}" not in allowed:
            return f"chunk:{cid}"
    raise RuntimeError("no spare chunk")


def corruptions(conn) -> list[dict]:
    """(name, expected failing check, applicable?, mutation). Each mutation takes (answer, gold, allowed)."""
    def deep(a):
        return json.loads(json.dumps(a))

    def add_cite(a, c):
        a = deep(a)
        a["citations"] = [*a.get("citations", []), c]
        return a

    def invented(a, g, al):
        a = deep(a)
        a["mappings"] = [*a.get("mappings", []), {"focal_id": "GV.OC-01", "reference_id": "ID.AM-4",
                                                    "note": "", "citations": ["xwalk:row4"]}]
        a["citations"] = [*a["citations"], "xwalk:row4"]
        return a

    def miscited(a, g, al):
        a = deep(a)
        m = a["mappings"][0]
        other = next(r for r in g["expected_crosswalk_rows"] if f"xwalk:row{r}" != m["citations"][0])
        m["citations"] = [f"xwalk:row{other}"]
        return a

    def wrong_version(a, g, al):
        other_v = "1.1" if g["allowed_versions"] == ["2.0"] else "2.0"
        return add_cite(a, _first_other_chunk(conn, al, other_v))

    def removal(a, g, al):
        a = deep(a)
        a["answer"] += " This control was removed from the framework."
        return a

    def drop_conflict(a, g, al):
        a = deep(a)
        drop = f"xwalk:row{g['conflict_rows'][-1]}"
        a["citations"] = [c for c in a["citations"] if c != drop]
        a["mappings"] = [m for m in a["mappings"] if drop not in m["citations"]]
        a["key_changes"] = [k for k in a["key_changes"] if drop not in k["citations"]]
        return a

    def invent_ref(a, g, al):
        a = deep(a)
        for m in a["mappings"]:
            if m["focal_id"] in g["expect_new"]:
                m["reference_id"] = "ID.AM-4"
        return a

    def forbidden_map(a, g, al):
        a = deep(a)
        a["mappings"] = [{"focal_id": "GV.OC-01", "reference_id": g["forbidden_mapping_controls"][0],
                          "note": "", "citations": ["xwalk:row4"]}]
        a["citations"] = [*a["citations"], "xwalk:row4"]
        return a

    def drop_row(a, g, al):
        a = deep(a)
        drop = f"xwalk:row{g['expected_crosswalk_rows'][0]}"
        a["citations"] = [c for c in a["citations"] if c != drop]
        a["mappings"] = [m for m in a["mappings"] if drop not in m["citations"]]
        a["key_changes"] = [k for k in a["key_changes"] if drop not in k["citations"]]
        return a

    def drop_control(a, g, al):
        a = deep(a)
        ids = {f"chunk:csf{c['version']}:" for c in g["expected_controls"]}
        a["citations"] = [c for c in a["citations"] if not any(c.startswith(i) and
                          any(c.endswith(":" + e["control_id"]) for e in g["expected_controls"])
                          for i in ids)]
        for e in g["expected_controls"]:
            a["answer"] = re.sub(re.escape(e["control_id"]), "the control", a["answer"], flags=re.IGNORECASE)
        for k in a["key_changes"]:
            for e in g["expected_controls"]:
                k["statement"] = re.sub(re.escape(e["control_id"]), "the control", k["statement"], flags=re.IGNORECASE)
        return a

    def answer_when_must_abstain(a, g, al):
        return {"answer": "The framework requires this.", "citations": [_first_other_chunk(conn, al)],
                "abstained": False}

    def abstain_wrongly(a, g, al):
        return {"answer": "", "abstained": True, "abstention_reason": "insufficient evidence"}

    def uncited(a, g, al):
        a = deep(a)
        a["key_changes"] = [*a.get("key_changes", []), {"statement": "Extra claim.", "citations": []}]
        return a

    def bad_structure(a, g, al):
        return ["not", "an", "object"]

    def ans(g):
        return not g["must_abstain"]

    return [
        {"name": "fabricated_citation", "check": "citation_ids_valid", "when": ans,
         "mutate": lambda a, g, al: add_cite(a, "chunk:csf2.0:subcategory:GV.ZZ-99")},
        {"name": "out_of_bundle_citation", "check": "citations_in_bundle", "when": ans,
         "mutate": lambda a, g, al: add_cite(a, _first_other_chunk(conn, al))},
        {"name": "invented_mapping", "check": "mapping_pairs_official", "when": ans, "mutate": invented},
        {"name": "miscited_mapping", "check": "mapping_cites_matching_row",
         "when": lambda g: not g["must_abstain"] and len(g["expected_mappings"]) >= 2, "mutate": miscited},
        {"name": "wrong_framework_version", "check": "versions_correct",
         "when": lambda g: not g["must_abstain"] and len(g["allowed_versions"]) == 1, "mutate": wrong_version},
        {"name": "unsupported_removal_claim", "check": "no_unsupported_removal", "when": ans,
         "mutate": removal},
        {"name": "dropped_conflict_row", "check": "conflict_preserved",
         "when": lambda g: bool(g["conflict_rows"]), "mutate": drop_conflict},
        {"name": "invented_reference_for_new_control", "check": "new_control_no_reference",
         "when": lambda g: bool(g["expect_new"]), "mutate": invent_ref},
        {"name": "mapping_for_unmapped_control", "check": "no_forbidden_mappings",
         "when": lambda g: bool(g["forbidden_mapping_controls"]), "mutate": forbidden_map},
        {"name": "missing_expected_row", "check": "expected_rows_covered",
         "when": lambda g: not g["must_abstain"] and g["row_coverage"] == "all"
         and len(g["expected_crosswalk_rows"]) >= 2, "mutate": drop_row},
        {"name": "missing_expected_control", "check": "expected_controls_referenced",
         "when": lambda g: not g["must_abstain"] and bool(g["expected_controls"]), "mutate": drop_control},
        {"name": "answer_instead_of_abstaining", "check": "abstention_correct",
         "when": lambda g: g["must_abstain"], "mutate": answer_when_must_abstain},
        {"name": "unwarranted_abstention", "check": "abstention_correct", "when": ans,
         "mutate": abstain_wrongly},
        {"name": "uncited_claim", "check": "no_uncited_claims", "when": ans, "mutate": uncited},
        {"name": "invalid_structure", "check": "schema_valid", "when": lambda g: True,
         "mutate": bad_structure},
    ]


def validator_self_test(gold: list[dict], conn: sqlite3.Connection) -> dict:
    """Does the checker accept gold-derived reference answers and flag each injected defect?
    This measures the CHECKER on synthetic fixtures. It says nothing about any language model."""
    accepted, built, fixture_failures = 0, 0, {}
    detect: dict[str, dict] = defaultdict(lambda: {"applicable": 0, "detected": 0, "missed": []})
    cors = corruptions(conn)
    for g in gold:
        fx = reference_fixture(g, conn)
        if fx is None:
            continue
        answer, allowed = fx
        built += 1
        base = check_answer(answer, g, conn, allowed)
        failed = [c["name"] for c in base if c["status"] == "fail"]
        if failed:
            fixture_failures[g["question_id"]] = failed
        else:
            accepted += 1
        for c in cors:
            if not c["when"](g) or failed:
                continue
            try:
                mutated = c["mutate"](answer, g, allowed)
            except (StopIteration, KeyError, IndexError, RuntimeError):
                continue
            res = check_answer(mutated, g, conn, allowed)
            d = detect[c["name"]]
            d["applicable"] += 1
            hit = any(r["name"] == c["check"] and r["status"] == "fail" for r in res)
            d["detected"] += hit
            if not hit:
                d["missed"].append(g["question_id"])
    return {"fixtures_built": built, "fixtures_accepted": accepted, "fixture_failures": fixture_failures,
            "corruptions": {k: dict(v) for k, v in sorted(detect.items())},
            "scope": "synthetic fixtures built from the gold file; measures the checker, not any model"}


# ================================================================== evidence-stage run + aggregation
def run_evidence_stage(gold: list[dict], assembler, store) -> dict:
    per_q = {}
    for g in gold:
        bundle = assembler.assemble(g["question"])
        checks = evidence_checks(bundle, g, store)
        per_q[g["question_id"]] = {"category": g["category"], "checks": checks,
                                   "bundle_summary": {
                                       "query_type": bundle.query_type,
                                       "searched_versions": bundle.searched_versions,
                                       "controls": [f"{r['control_id']}@{r['version']}" for r in bundle.control_records],
                                       "crosswalk_rows": sorted(r["excel_row"] for r in bundle.crosswalk_records),
                                       "n_passages": len(bundle.passages),
                                       "conflicts": [c["control_id"] for c in bundle.conflicts],
                                       "unmapped": [u["control_id"] for u in bundle.unmapped_controls],
                                       "missing_evidence": [m["kind"] for m in bundle.missing_evidence]},
                                   "all_passed": all(c["status"] != "fail" for c in checks)}
    return {"per_question": per_q, "aggregate": aggregate(per_q)}


def aggregate(per_q: dict) -> dict:
    """Pass rates per check (n/a excluded) and per category; a question passes if no check failed."""
    by_check: dict[str, Counter] = defaultdict(Counter)
    by_cat: dict[str, Counter] = defaultdict(Counter)
    for r in per_q.values():
        for c in r["checks"]:
            by_check[c["name"]][c["status"]] += 1
        by_cat[r["category"]]["pass" if r["all_passed"] else "fail"] += 1
    checks = {}
    for n, c in by_check.items():
        app = c["pass"] + c["fail"]
        checks[n] = {"applicable": app, "passed": c["pass"], "failed": c["fail"],
                     "pass_rate": (c["pass"] / app) if app else None}
    total = len(per_q)
    return {"n_questions": total, "questions_all_checks_passed": sum(r["all_passed"] for r in per_q.values()),
            "per_check": dict(sorted(checks.items())),
            "per_category": {k: {"questions": v["pass"] + v["fail"], "all_passed": v["pass"]}
                             for k, v in sorted(by_cat.items())},
            "failed_questions": sorted(q for q, r in per_q.items() if not r["all_passed"])}


# ================================================================== optional live mode (off by default)
def run_live(gold: list[dict], assembler, store, provider, settings, limit: int,
             reviews: dict | None = None) -> dict:
    """Generate answers with `provider` and run the deterministic checks on them. Callers must have
    opted in explicitly (see eval/answer_eval.py). `is_live_model` is true only for a real provider,
    so results from a fake provider can never be mistaken for model accuracy."""
    from ..generation.generate import GroundedGenerator

    per_q = {}
    for g in gold[:limit]:
        if g.get("invalid_input"):  # the API would answer HTTP 422; no pipeline run, no model call
            per_q[g["question_id"]] = {"category": g["category"], "status": "rejected_before_pipeline",
                                       "rejection": [], "answer": None, "attempts": 0, "checks": [],
                                       "all_passed": False}
            continue
        bundle = assembler.assemble(g["question"])
        res = GroundedGenerator(provider, settings).generate(bundle, store)
        entry = {"category": g["category"], "status": res.status, "rejection": res.rejection,
                 "answer": res.answer, "attempts": res.attempts}
        if res.status == "evidence_only":
            entry["checks"] = []
        elif res.answer is not None:
            entry["checks"] = check_answer(res.answer, g, store.conn, set(bundle.citations))
        elif res.status == "abstained":  # deterministic abstention (no LLM call)
            entry["checks"] = check_answer({"answer": "", "abstained": True,
                                            "abstention_reason": res.abstention_reason}, g, store.conn,
                                           set(bundle.citations))
        else:
            entry["checks"] = [result("answer_produced", "structural", "fail",
                                      "; ".join(res.rejection)[:200] or res.status)]
        entry["all_passed"] = bool(entry["checks"]) and all(c["status"] != "fail" for c in entry["checks"])
        per_q[g["question_id"]] = entry
    return {"provider": getattr(provider, "name", "unknown"), "model": getattr(provider, "model", None),
            "is_live_model": getattr(provider, "name", "") in ("gemini", "mistral"), "questions_run": len(per_q),
            "per_question": per_q, "aggregate": aggregate({k: v for k, v in per_q.items() if v["checks"]}),
            "semantic_faithfulness": SEMANTIC}


# ================================================================== review tracking
class ReviewError(ValueError):
    pass


def blank_review() -> dict:
    return {"status": "pending", "groundedness": None, "completeness": None, "reviewer": None, "notes": ""}


def validate_review(r: dict) -> None:
    if r.get("status") not in ("pending", "reviewed"):
        raise ReviewError(f"bad status {r.get('status')!r}")
    if r["groundedness"] is not None and r["groundedness"] not in GROUNDEDNESS:
        raise ReviewError(f"bad groundedness {r['groundedness']!r}")
    if r["completeness"] is not None and r["completeness"] not in COMPLETENESS:
        raise ReviewError(f"bad completeness {r['completeness']!r}")
    if r["status"] == "reviewed" and not (r["groundedness"] and r["completeness"] and r.get("reviewer")):
        raise ReviewError("a reviewed entry needs groundedness, completeness and a reviewer name")
    if r["status"] == "pending" and (r["groundedness"] or r["completeness"]):
        raise ReviewError("scores may only be set on a reviewed entry")


def load_reviews(path: Path, question_ids: list[str]) -> dict:
    """Existing reviewer input is preserved; new questions start as pending."""
    existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    out = {}
    for q in question_ids:
        r = existing.get(q, blank_review())
        validate_review(r)
        out[q] = r
    return out


def review_summary(reviews: dict) -> dict:
    reviewed = [r for r in reviews.values() if r["status"] == "reviewed"]
    return {"total": len(reviews), "pending": len(reviews) - len(reviewed), "reviewed": len(reviewed),
            "groundedness": dict(Counter(r["groundedness"] for r in reviewed)),
            "completeness": dict(Counter(r["completeness"] for r in reviewed))}

