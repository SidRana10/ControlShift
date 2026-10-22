"""Builds eval/answer_questions.jsonl, the gold file for grounded-answer evaluation.

Expectations are derived from the stored NIST text and the official crosswalk rows (SQLite), never
from model output. Crosswalk row sets are looked up in the database by control ID; quoted facts are
checked as substrings of the stored chunk text; "absent" topics are checked to occur nowhere in the
corpus. All of this is AI-curated and NOT human-reviewed.

    python eval/build_answer_questions.py [--db data/processed/controlshift.db]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from controlshift.evaluation.answers import (
    PROVENANCE,
    validate_gold_against_db,
    validate_gold_schema,
)
from controlshift.store.schema import connect

BOTH = ["1.1", "2.0"]


def rows_by(conn, field: str, control_id: str) -> list[dict]:
    col = {"focal": "focal_original_id", "reference": "reference_original_id"}[field]
    return [{"row": r[0], "focal": r[1], "reference": r[2]} for r in conn.execute(
        f"SELECT excel_row, focal_original_id, reference_original_id FROM crosswalk_mapping "
        f"WHERE {col}=? ORDER BY excel_row", (control_id,))]


def text_fact(statement: str, chunk_id: str, quote: str) -> dict:
    return {"type": "text", "statement": statement, "evidence": f"chunk:{chunk_id}", "quote": quote}


def map_facts(mappings: list[dict]) -> list[dict]:
    return [{"type": "mapping", "statement": f"Official row {m['row']}: {m['focal']} -> "
             f"{m['reference'] or 'no CSF 1.1 reference (conceptually new in 2.0)'}",
             "evidence": f"xwalk:row{m['row']}", "row": m["row"]} for m in mappings]


def record(qid, cat, question, qtype, *, controls=(), mappings=(), extra_rows=(), conflict=(), invalid=False, justification="", related=None,
           new=(), forbidden=(), versions=BOTH, abstain=False, basis=None, absent=(), facts=(),
           conditions="", coverage="all", unresolved=(), notes=""):
    rows = sorted({m["row"] for m in mappings} | set(extra_rows))
    return {
        "question_id": qid, "category": cat, "question": question, "expected_query_type": qtype,
        "expected_controls": [{"control_id": c, "version": v} for c, v in controls],
        "expected_crosswalk_rows": rows, "expected_mappings": list(mappings),
        "conflict_rows": list(conflict), "expect_new": list(new),
        "forbidden_mapping_controls": list(forbidden), "allowed_versions": list(versions),
        "must_abstain": abstain, "abstention_basis": basis, "absent_terms": list(absent),
        "expected_facts": [*facts, *map_facts(list(mappings))], "abstention_conditions": conditions,
        "row_coverage": coverage, "expected_unresolved": list(unresolved), "notes": notes,
        "invalid_input": invalid, "expected_api_status": 422 if invalid else None,
        "abstention_justification": justification, "reviewed_related_terms": related or {},
        "review": {"label_provenance": PROVENANCE, "human_reviewed": False},
    }


def build(db: Path) -> list[dict]:
    conn = connect(db, readonly=True)
    new_rows = [{"row": r[0], "focal": r[1], "reference": None} for r in conn.execute(
        "SELECT excel_row, focal_original_id FROM crosswalk_mapping WHERE mapping_type='new_in_2_0' "
        "ORDER BY excel_row")]
    unreferenced = [r[0] for r in conn.execute(
        "SELECT e.original_id FROM element e WHERE e.version='1.1' AND e.level='subcategory' AND NOT "
        "EXISTS (SELECT 1 FROM crosswalk_mapping m WHERE m.reference_element_id=e.element_id) "
        "ORDER BY e.element_id")]
    if not unreferenced:
        sys.exit("no unreferenced CSF 1.1 subcategory found")
    unmapped_11 = unreferenced[0]
    gv_sc_03 = rows_by(conn, "focal", "GV.SC-03")
    out = [
        record("A01", "exact_control", "What does GV.SC-03 require?", "single_version",
               controls=[("GV.SC-03", "2.0")], versions=["2.0"],
               facts=[text_fact("GV.SC-03 integrates supply chain risk management into broader risk processes.",
                                "csf2.0:subcategory:GV.SC-03",
                                "Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes")]),
        record("A02", "exact_control", "What does PR.AT-1 require in CSF 1.1?", "single_version",
               controls=[("PR.AT-1", "1.1")], versions=["1.1"],
               facts=[text_fact("CSF 1.1 PR.AT-1: all users are informed and trained.",
                                "csf1.1:subcategory:PR.AT-1", "All users are informed and trained")]),
        record("A03", "exact_control", "Explain DE.CM-01", "single_version",
               controls=[("DE.CM-01", "2.0"), ("DE.CM-1", "1.1")],
               unresolved=["exists in both CSF versions"],
               facts=[text_fact("CSF 2.0 DE.CM-01 monitors networks and network services.",
                                "csf2.0:subcategory:DE.CM-01",
                                "Networks and network services are monitored to find potentially adverse events"),
                      text_fact("CSF 1.1 DE.CM-1 monitors the network.", "csf1.1:subcategory:DE.CM-1",
                                "The network is monitored to detect potential cybersecurity events")],
               notes="The normalised ID DE.CM-01 exists in both versions; no version is named, so both must be reported."),
        record("B01", "comparison", "What are the differences between CSF 1.1 and 2.0 for supply chain risk management?",
               "cross_version_comparison", mappings=rows_by(conn, "focal", "GV.SC")[:1], coverage="any",
               notes="Row 22 maps the 2.0 category GV.SC to the 1.1 category ID.SC. Whether the pipeline's evidence "
                     "includes it depends on retrieval."),
        record("B02", "comparison", "Compare CSF 1.1 and 2.0 on risk tolerance and risk appetite statements",
               "cross_version_comparison", mappings=rows_by(conn, "focal", "GV.RM-02"), coverage="any",
               notes="Rows 15-16 map GV.RM-02 to ID.RM-2 and ID.RM-3."),
        record("B03", "comparison", "What is new in CSF 2.0?", "cross_version_comparison",
               mappings=new_rows, coverage="any", new=[],
               notes="All 20 rows marked 'Conceptually new in 2.0' should be in the evidence; an answer need not cite all."),
        record("C01", "official_mapping", "How does GV.OC-01 map to CSF 1.1?", "control_mapping",
               controls=[("GV.OC-01", "2.0"), ("ID.BE-2", "1.1"), ("ID.BE-3", "1.1")],
               mappings=rows_by(conn, "focal", "GV.OC-01")),
        record("C02", "official_mapping", "Which CSF 2.0 controls correspond to ID.BE-2?", "control_mapping",
               controls=[("ID.BE-2", "1.1"), ("GV.OC-01", "2.0")], mappings=rows_by(conn, "reference", "ID.BE-2")),
        record("C03", "official_mapping", "How does PR.DS-01 map to CSF 1.1?", "control_mapping",
               controls=[("PR.DS-01", "2.0"), ("PR.DS-1", "1.1")], mappings=rows_by(conn, "focal", "PR.DS-01")),
        record("D01", "one_to_many", "Which CSF 1.1 controls does GV.RR-02 map to?", "control_mapping",
               controls=[("GV.RR-02", "2.0"), ("ID.AM-6", "1.1")], mappings=rows_by(conn, "focal", "GV.RR-02")),
        record("D02", "one_to_many", "Which CSF 2.0 controls correspond to ID.SC-1?", "control_mapping",
               controls=[("ID.SC-1", "1.1")], mappings=rows_by(conn, "reference", "ID.SC-1"),
               notes="Many-to-one on the 1.1 side (five 2.0 controls)."),
        record("E01", "conceptually_new", "How does GV.OV-01 map to CSF 1.1?", "control_mapping",
               controls=[("GV.OV-01", "2.0")], mappings=rows_by(conn, "focal", "GV.OV-01"), new=["GV.OV-01"]),
        record("E02", "conceptually_new", "How does RC.RP-04 map to CSF 1.1?", "control_mapping",
               controls=[("RC.RP-04", "2.0")], mappings=rows_by(conn, "focal", "RC.RP-04"), new=["RC.RP-04"]),
        record("F01", "conflict", "How does GV.SC-03 map to CSF 1.1?", "control_mapping",
               controls=[("GV.SC-03", "2.0"), ("ID.SC-2", "1.1")], mappings=gv_sc_03,
               conflict=[m["row"] for m in gv_sc_03],
               notes="Official workbook holds a mapped row (to ID.SC-2) and a 'conceptually new' row for GV.SC-03."),
        record("F02", "conflict", "Does GV.SC-03 have an equivalent in CSF 1.1?", "control_mapping",
               controls=[("GV.SC-03", "2.0"), ("ID.SC-2", "1.1")], mappings=gv_sc_03,
               conflict=[m["row"] for m in gv_sc_03]),
        record("G01", "missing_mapping", f"How does {unmapped_11} map to CSF 2.0?", "control_mapping",
               controls=[(unmapped_11, "1.1")], forbidden=[unmapped_11],
               facts=[text_fact(f"{unmapped_11} exists in CSF 1.1.", f"csf1.1:subcategory:{unmapped_11}", "Reputation is repaired after an incident")],
               notes="No crosswalk row references this 1.1 control; absence must not be read as 'removed'."),
        record("H01", "abstention", "What replaced GV.XX-99 in CSF 2.0?", "control_mapping", abstain=True,
               basis="control_not_found", conditions="The control ID GV.XX-99 does not exist in either version."),
        record("H02", "abstention", "Which CSF control requires quantum-safe cryptography?", "single_version",
               abstain=True, basis="topic_absent",
               absent=["quantum", "post-quantum", "cryptograph", "encrypt", "crypto"],
               justification="Not just the word 'quantum': the stored NIST text never mentions cryptography, "
                             "encryption or any cryptographic algorithm in either version (0 chunks for each term), "
                             "so no passage can say which control requires quantum-safe cryptography.",
               conditions="The corpus has no cryptography content at all; any retrieved passage is off-topic."),
        record("H03", "abstention", "What is the penalty for failing to implement GV.SC-03?", "single_version",
               abstain=True, basis="topic_absent",
               absent=["penalt", "sanction", "punish", "consequence", "noncompliance", "non-compliance"],
               justification="GV.SC-03 exists (its text is in the evidence) but neither CSF document states any penalty, "
                             "sanction or consequence for non-implementation (0 chunks for each concept term). The nearest "
                             "passages (CSF 1.1 remarks on 'compliance' and that the Framework is voluntary) were read and "
                             "do not define penalties. A reply that says the documents define no penalty is a legitimate "
                             "alternative to a flat abstention; the automatic check is deliberately strict (see notes).",
               related={"compliance": {"chunks": 5, "note": "CSF 1.1 text discussing the word 'compliance' with the Framework and privacy-law compliance; no penalty is defined."},
                        "voluntary": {"chunks": 3, "note": "CSF 1.1 says the Framework is voluntary and RS.CO-5 mentions voluntary sharing; no penalty is defined."},
                        "enforc": {"chunks": 7, "note": "'enforced' in 2.0 policy/access outcomes and 'law enforcement' in 1.1 RS.CO; none concerns penalties for not implementing a control."},
                        "liabilit": {"chunks": 1, "note": "'reliability' (substring match) in CSF 1.1 ICS text; unrelated."}},
               conditions="The question presumes a penalty regime that the documents do not contain.",
               controls=[("GV.SC-03", "2.0")],
               notes="Strict check: only an explicit abstention counts as a pass."),
        record("H04", "invalid_input", "   ", "unsupported", invalid=True,
               conditions="A blank question is invalid input: the API answers HTTP 422 and never retrieves or generates. "
                          "It is NOT an evidence-based abstention.",
               notes="If a blank question reached the pipeline anyway it would be classified 'unsupported' and abstain "
                     "without a model call (defence in depth)."),
    ]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--out", type=Path, default=Path("eval/answer_questions.jsonl"))
    args = ap.parse_args()
    gold = build(args.db)
    errors = validate_gold_schema(gold) + validate_gold_against_db(gold, args.db)
    if errors:
        sys.exit("gold dataset invalid:\n" + "\n".join(errors))
    args.out.write_text("".join(json.dumps(g, ensure_ascii=False) + "\n" for g in gold), encoding="utf-8")
    print(f"wrote {len(gold)} gold questions to {args.out}")


if __name__ == "__main__":
    main()
