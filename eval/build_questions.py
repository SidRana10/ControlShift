"""Builds eval/questions.jsonl and eval/questions_audit.md from the curated specification below.

The relevance judgments in SPEC were written by an AI assistant (Claude) by reading the stored
source text (NIST CSF 1.1 / 2.0 PDFs as ingested) and, for cross-version pairs, the official NIST
crosswalk rows. NO retrieval system output was used to choose or grade them. They have NOT been
reviewed by a human. The script only attaches provenance (page, source file, excerpt) from the
database and fails if a chunk ID does not exist.

    python eval/build_questions.py [--db data/processed/controlshift.db]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from controlshift.evaluation.dataset import PROVENANCE, parse_query, validate
from controlshift.store.schema import connect


def c1(i, kind="subcategory"):
    return f"csf1.1:{kind}:{i}"


def c2(i, kind="subcategory"):
    return f"csf2.0:{kind}:{i}"


def t1(h):
    return f"csf1.1:text:{h}"


def t2(h):
    return f"csf2.0:text:{h}"


# (query_id, category, difficulty, question, version_filter, status, [(chunk_id, grade, why)], notes)
SPEC = [
    # ---------------------------------------------------------------- exact control IDs
    ("E01", "exact_id", "easy", "GV.SC-03", "2.0", "final",
     [(c2("GV.SC-03"), 2, "The CSF 2.0 subcategory with exactly this ID.")], ""),
    ("E02", "exact_id", "easy", "PR.AT-1", "1.1", "final",
     [(c1("PR.AT-1"), 2, "The CSF 1.1 subcategory PR.AT-1 (unpadded 1.1 spelling).")], ""),
    ("E03", "exact_id", "medium", "ID.AM-1", None, "final",
     [(c1("ID.AM-1"), 2, "CSF 1.1 subcategory ID.AM-1 (physical devices inventoried)."),
      (c2("ID.AM-01"), 2, "CSF 2.0 ID.AM-01 normalises to the same ID and the official crosswalk "
                          "row 51 maps ID.AM-01 to ID.AM-1; no version was requested.")],
     "Unfiltered ID query: both versions' controls carry this normalised ID."),
    ("E04", "exact_id", "easy", "DE.CM-01", "2.0", "final",
     [(c2("DE.CM-01"), 2, "The CSF 2.0 subcategory with exactly this ID.")], ""),
    ("E05", "exact_id", "easy", "RS.MA-02", "2.0", "final",
     [(c2("RS.MA-02"), 2, "The CSF 2.0 subcategory with exactly this ID (incident reports triaged).")], ""),
    ("E06", "exact_id", "easy", "PR.DS-10", "2.0", "final",
     [(c2("PR.DS-10"), 2, "The CSF 2.0 subcategory PR.DS-10 (data-in-use). Number is not sequential.")], ""),
    ("E07", "exact_id", "medium", "RC.RP-3", "2.0", "final",
     [(c2("RC.RP-03"), 2, "User wrote the unpadded spelling; the 2.0 control is RC.RP-03.")], "ID spelling variant."),
    ("E08", "exact_id", "medium", "ID.SC", "1.1", "final",
     [(c1("ID.SC", "category"), 2, "The CSF 1.1 category chunk with this identifier.")],
     "Category-level ID; its subcategories are plausible near-misses but not labelled."),
    ("E09", "exact_id", "medium", "GV.OV", "2.0", "final",
     [(c2("GV.OV", "category"), 2, "The CSF 2.0 Oversight category chunk with this identifier.")], ""),
    ("E10", "exact_id", "easy", "DE.AE-5", "1.1", "final",
     [(c1("DE.AE-5"), 2, "The CSF 1.1 subcategory DE.AE-5 (incident alert thresholds).")], ""),
    ("E11", "exact_id", "medium", "What does PR.AC-7 require?", "1.1", "final",
     [(c1("PR.AC-7"), 2, "ID embedded in a natural-language question; PR.AC-7 in CSF 1.1.")], ""),
    # ---------------------------------------------------------------- semantic questions
    ("S01", "semantic", "easy", "How should an organization protect data that is stored on disks and in databases?", None, "final",
     [(c1("PR.DS-1"), 2, "PR.DS-1 'Data-at-rest is protected'."),
      (c2("PR.DS-01"), 2, "PR.DS-01 protects confidentiality, integrity and availability of data-at-rest; crosswalk row 119 maps it to PR.DS-1.")],
     "Paraphrase of 'data at rest' without the term."),
    ("S02", "semantic", "medium", "Which outcome requires users and devices to be authenticated, for example with multi-factor authentication?", None, "final",
     [(c1("PR.AC-7"), 2, "States users, devices and assets are authenticated (e.g., single-factor, multi-factor)."),
      (c2("PR.AA-03"), 1, "2.0 'Users, services, and hardware are authenticated'; no MFA wording, linked to PR.AC-7 by crosswalk row 103.")], ""),
    ("S03", "semantic", "easy", "Backups should be created and checked regularly to make sure they can be restored.", None, "final",
     [(c1("PR.IP-4"), 2, "PR.IP-4 'Backups of information are conducted, maintained, and tested'."),
      (c2("PR.DS-11"), 2, "PR.DS-11 'Backups of data are created, protected, maintained, and tested'; crosswalk row 126.")], ""),
    ("S04", "semantic", "easy", "Keeping an inventory of the physical computers and devices an organization owns", None, "final",
     [(c1("ID.AM-1"), 2, "ID.AM-1 'Physical devices and systems ... are inventoried'."),
      (c2("ID.AM-01"), 2, "ID.AM-01 'Inventories of hardware managed by the organization are maintained'.")], ""),
    ("S05", "semantic", "medium", "How should an organization handle security weaknesses reported to it by outside researchers?", None, "final",
     [(c1("RS.AN-5"), 2, "RS.AN-5 processes to receive, analyze and respond to vulnerabilities disclosed to the organization."),
      (c2("ID.RA-08"), 2, "ID.RA-08 processes for receiving, analyzing and responding to vulnerability disclosures; crosswalk row 75.")],
     "No lexical overlap with 'disclosure'."),
    ("S06", "semantic", "easy", "Receiving cyber threat intelligence from information sharing groups", None, "final",
     [(c1("ID.RA-2"), 2, "ID.RA-2 threat intelligence from information sharing forums and sources."),
      (c2("ID.RA-02"), 2, "ID.RA-02 same wording; crosswalk row 68.")], ""),
    ("S07", "semantic", "easy", "Stopping a cybersecurity incident from spreading further", None, "final",
     [(c1("RS.MI-1"), 2, "RS.MI-1 'Incidents are contained'."),
      (c2("RS.MI-01"), 2, "RS.MI-01 'Incidents are contained'; crosswalk row 193.")], ""),
    ("S08", "semantic", "hard", "How are response and recovery plans improved using lessons learned from incidents?", None, "provisional",
     [(c1("RS.IM-1"), 2, "RS.IM-1 'Response plans incorporate lessons learned'."),
      (c1("RC.IM-1"), 2, "RC.IM-1 'Recovery plans incorporate lessons learned'."),
      (c2("ID.IM-04"), 1, "ID.IM-04 plans ... maintained and improved; crosswalk rows 95-96 link RS.IM-1/RC.IM-1."),
      (c2("ID.IM-03"), 1, "ID.IM-03 improvements from operational activities; crosswalk rows 90, 92.")],
     "PROVISIONAL: several 2.0 controls are plausible and the grading of which counts is uncertain."),
    ("S09", "semantic", "medium", "What does the framework say about keeping audit trails and logs of system activity?", None, "final",
     [(c1("PR.PT-1"), 2, "PR.PT-1 audit/log records are determined, documented, implemented and reviewed."),
      (c2("PR.PS-04"), 2, "PR.PS-04 log records are generated and made available for continuous monitoring; crosswalk row 136.")], ""),
    ("S10", "semantic", "hard", "Development and testing systems should be kept apart from live production systems.", None, "final",
     [(c1("PR.DS-7"), 2, "PR.DS-7 'development and testing environment(s) are separate from the production environment'."),
      (c2("PR.IR-01"), 1, "PR.IR-01 protects networks and environments; crosswalk row 142 maps PR.DS-7 here, but no explicit separation wording.")], ""),
    # ---------------------------------------------------------------- version-specific
    ("V01", "version_specific", "medium", "Which outcome covers reviewing the risk management strategy to make sure it still covers the organization's requirements and risks?", "2.0", "final",
     [(c2("GV.OV-02"), 2, "GV.OV-02 strategy 'reviewed and adjusted to ensure coverage of organizational requirements and risks'."),
      (c2("GV.OV-01"), 1, "GV.OV-01 strategy outcomes reviewed to inform and adjust strategy."),
      (c2("GV.OV-03"), 1, "GV.OV-03 performance evaluated and reviewed for needed adjustments.")], ""),
    ("V02", "version_specific", "medium", "Who is accountable for cybersecurity risk and builds a risk-aware culture?", "2.0", "final",
     [(c2("GV.RR-01"), 2, "GV.RR-01 organizational leadership is responsible and accountable and fosters a risk-aware culture.")], ""),
    ("V03", "version_specific", "medium", "What is the purpose of the GOVERN function?", "2.0", "final",
     [(t2("0105534cd143"), 2, "Narrative defining GOVERN (GV) and what the Function provides."),
      (c2("GV", "function"), 2, "Function chunk 'GOVERN (GV): ... strategy, expectations, and policy are established, communicated, and monitored'."),
      (t2("00c7e5b2ba7b"), 1, "Explains how the GOVERN Function supports risk communication with executives.")], ""),
    ("V04", "version_specific", "easy", "What are the six Functions of the CSF Core?", "2.0", "final",
     [(t2("2400d2aa8dcf"), 2, "Lists 'GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, and RECOVER' (verified by substring)."),
      (t2("8962e17152b8"), 1, "Glossary chunk that also lists the six Functions.")], ""),
    ("V05", "version_specific", "easy", "What are the five Functions of the Framework Core?", "1.1", "final",
     [(t1("b1fe485caf83"), 2, "Section 2.1 states the Functions: Identify, Protect, Detect, Respond, and Recover (verified by substring)."),
      (t1("d1930b34ffdb"), 1, "Section 3.1 repeats the five Functions."),
      (t1("dddb82324e42"), 1, "Glossary entry listing the five Functions.")], ""),
    ("V06", "version_specific", "medium", "How does the Framework describe the Implementation Tiers?", "1.1", "final",
     [(t1("28bf886ec726"), 2, "Defines Tiers from Partial (Tier 1) to Adaptive (Tier 4)."),
      (t1("4cd53030c0a8"), 1, "Describes the Tier selection process.")], ""),
    ("V07", "version_specific", "easy", "What is a Community Profile?", "2.0", "final",
     [(t2("1e8b583f99d6"), 2, "Defines a Community Profile as a baseline of CSF outcomes for shared interests."),
      (t2("8962e17152b8"), 1, "Glossary chunk containing the Community Profile definition.")], ""),
    ("V08", "version_specific", "medium", "How does the CSF relate to artificial intelligence risks?", "2.0", "final",
     [(t2("752c4811c287"), 2, "Bullet on risks from emerging technologies, AI and the NIST AI RMF."),
      (t2("ce65b06e28e0"), 1, "Lists AI among the ICT risks addressed alongside enterprise risk management.")], ""),
    ("V09", "version_specific", "hard", "What methodology does the Framework describe for protecting privacy and civil liberties?", "1.1", "final",
     [(t1("c892f6549390"), 2, "Introduces the privacy and civil liberties methodology."),
      (t1("c8cf37e0d42a"), 2, "Privacy principles to incorporate (data minimization, etc.)."),
      (t1("11c75e8ed0b8"), 1, "Continues the methodology bullets (privacy responsibilities, compliance processes).")], ""),
    ("V10", "version_specific", "hard", "Which outcome sets post-incident operating norms based on critical mission functions?", "2.0", "final",
     [(c2("RC.RP-04"), 2, "RC.RP-04 'Critical mission functions and cybersecurity risk management are considered to establish post-incident operational norms'.")], ""),
    ("V11", "version_specific", "medium", "How can a Target Profile help with decisions about buying products and services?", "1.1", "final",
     [(t1("4aaca68a5ca1"), 2, "Section 3.4 Buying Decisions: Target Profiles inform buying decisions.")], ""),
    # ---------------------------------------------------------------- cross-version
    ("X01", "cross_version", "medium", "proofing identities and binding them to credentials", None, "final",
     [(c1("PR.AC-6"), 2, "PR.AC-6 identities proofed and bound to credentials."),
      (c2("PR.AA-02"), 2, "PR.AA-02 same outcome, 2.0 wording; crosswalk row 101.")], ""),
    ("X02", "cross_version", "medium", "executing the recovery plan during or after a cybersecurity incident", None, "final",
     [(c1("RC.RP-1"), 2, "RC.RP-1 recovery plan is executed during or after an incident."),
      (c2("RC.RP-01"), 2, "RC.RP-01 recovery portion of the IR plan is executed; crosswalk row 197.")], ""),
    ("X03", "cross_version", "hard", "knowing which suppliers matter most and ranking them by how critical they are", None, "final",
     [(c1("ID.SC-2"), 2, "ID.SC-2 suppliers and third parties identified, prioritized and assessed."),
      (c2("GV.SC-04"), 2, "GV.SC-04 'Suppliers are known and prioritized by criticality'; crosswalk row 27.")], ""),
    ("X04", "cross_version", "medium", "risk tolerance and risk appetite statements", None, "final",
     [(c1("ID.RM-2"), 2, "ID.RM-2 organizational risk tolerance is determined and clearly expressed."),
      (c2("GV.RM-02"), 2, "GV.RM-02 risk appetite and risk tolerance statements; crosswalk row 15.")], ""),
    ("X05", "cross_version", "hard", "cybersecurity responsibilities of the whole workforce and outside partners", None, "final",
     [(c1("ID.AM-6"), 2, "ID.AM-6 roles and responsibilities for the entire workforce and third-party stakeholders."),
      (c2("GV.RR-02"), 2, "GV.RR-02 roles, responsibilities and authorities established; crosswalk row 37 maps ID.AM-6 here.")], ""),
    ("X06", "cross_version", "medium", "legal and regulatory obligations including privacy and civil liberties", None, "final",
     [(c1("ID.GV-3"), 2, "ID.GV-3 legal and regulatory requirements incl. privacy and civil liberties."),
      (c2("GV.OC-03"), 2, "GV.OC-03 legal, regulatory and contractual requirements incl. privacy and civil liberties; crosswalk row 8.")], ""),
    ("X07", "cross_version", "medium", "collecting and correlating event data from several sources", None, "final",
     [(c1("DE.AE-3"), 2, "DE.AE-3 event data collected and correlated from multiple sources and sensors."),
      (c2("DE.AE-03"), 2, "DE.AE-03 information is correlated from multiple sources; crosswalk row 166.")], ""),
    ("X08", "cross_version", "hard", "What are the Tier levels and their names?", None, "final",
     [(t1("28bf886ec726"), 2, "CSF 1.1 Tiers from Partial (Tier 1) to Adaptive (Tier 4)."),
      (t2("6a6b15d78865"), 2, "CSF 2.0 Tiers: Partial, Risk Informed, Repeatable, Adaptive.")], ""),
]


def build(db_path: Path) -> list[dict]:
    conn = connect(db_path, readonly=True)
    records = []
    for qid, cat, diff, question, vfilter, status, rel, notes in SPEC:
        items = []
        for chunk_id, grade, why in rel:
            row = conn.execute(
                "SELECT c.version, c.source_file, c.page, c.section, c.text, e.original_id "
                "FROM chunk c LEFT JOIN element e ON e.version=c.version AND "
                "e.element_id=c.element_id WHERE c.chunk_id=?", (chunk_id,)).fetchone()
            if row is None:
                sys.exit(f"{qid}: chunk {chunk_id} does not exist in the database")
            items.append({"chunk_id": chunk_id, "grade": grade, "version": row["version"],
                          "control_id": row["original_id"], "source_file": row["source_file"],
                          "page": row["page"], "section": row["section"],
                          "source_excerpt": row["text"][:160], "why": why})
        records.append({"query_id": qid, "question": question, "category": cat,
                        "difficulty": diff, "version_filter": vfilter, "status": status,
                        "label_provenance": PROVENANCE, "human_reviewed": False,
                        "relevant": items, "notes": notes})
    return records


def audit_markdown(records: list[dict]) -> str:
    out = ["# Evaluation question audit sheet", "",
           "**Label provenance:** every judgment below was written by an AI assistant (Claude) from the "
           "stored source text and, for cross-version pairs, the official NIST crosswalk rows. "
           "No retrieval output was used. **No human has reviewed these labels.** Grade 2 = highly "
           "relevant, grade 1 = relevant. `provisional` queries are excluded from headline metrics.", ""]
    for r in records:
        flt = r["version_filter"] or "none"
        out += [f"## {r['query_id']} - {r['question']}", "",
                f"- category: `{r['category']}`  difficulty: `{r['difficulty']}`  version filter: `{flt}`  "
                f"status: **{r['status']}**" + (f"  \n- notes: {r['notes']}" if r["notes"] else ""), ""]
        for x in r["relevant"]:
            ctl = f" {x['control_id']}" if x["control_id"] else ""
            out += [f"- **grade {x['grade']}** `{x['chunk_id']}` (CSF {x['version']}{ctl}, "
                    f"{x['source_file']} p.{x['page']}, {x['section']})",
                    f"  - why: {x['why']}", f"  - source: \"{x['source_excerpt'].replace(chr(10), ' ')}\""]
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--out-dir", type=Path, default=Path("eval"))
    args = ap.parse_args()
    records = build(args.db)
    queries = [parse_query(r) for r in records]
    errors = validate(queries, args.db)
    if errors:
        sys.exit("dataset invalid:\n" + "\n".join(errors))
    (args.out_dir / "questions.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    (args.out_dir / "questions_audit.md").write_text(audit_markdown(records), encoding="utf-8")
    print(f"wrote {len(records)} questions to {args.out_dir}/questions.jsonl and questions_audit.md")


if __name__ == "__main__":
    main()
