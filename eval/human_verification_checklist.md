# Human verification checklist — six live RAG answers (NOT completed by a human; reviewer fields intentionally blank)

**Status:** the exploratory evaluation phase was closed by the developer *without* a completed independent checklist. This file stays as an **optional future human-calibration aid**; nothing in it is signed off, and the AI-assisted original-source check is described in the packet.

**For the developer.** Everything marked [AI] is a preliminary reading; [M] is machine-verified; [J] is the GPT-OSS judge; **[H] is yours to confirm and nothing has been confirmed yet.**
Open the *original* NIST files (`nist_csf_1_1.pdf`, `nist_csf_2_0.pdf`, `nist_csf_transition.xlsx`, sheet `Relationships`) — the database is derived from them, so an ingestion slip would not show up if you only
read the database. Answers and excerpts: `eval/human_review_packet.md`. B01 comparison: `eval/b01_before_after.md`. PDF page numbers below are PDF pages (printed page in brackets).

**Citation methodology:** *claim-level evidence support* (does an authoritative citation support the claim?) and *per-citation precision* (does each attached citation support it?) are kept separate.

**Citation support — decide once (applies to A01, C01, F01, E01):** is it *claim-level* (an official row supports the mapping claim) or *per-citation precision* (every attached citation must support it)?
Judge scores (unchanged): A01 5/5, C01 2/5, F01 3/5, E01 4/5. ☐ claim-level  ☐ per-citation  ☐ other: ______  Reviewer ______ Date ______

---
## A01 — What does GV.SC-03 require?
- **Claims to verify:** GV.SC-03 requires that cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes.
- **Sources:** CSF 2.0 GV.SC-03 — `nist_csf_2_0.pdf` p.22 [17] (`chunk:csf2.0:subcategory:GV.SC-03`).
- **Preliminary [AI]:** correct, faithful, complete. [M] all applicable checks pass. [J] 5/5 on all five dimensions.
- **Disputed / unsupported:** none identified.
- ☐ Correct  ☐ Faithful to the cited text  ☐ Complete  ☐ Citation supports claim  ☐ Relevant  ☐ Disagree (see notes)
- Reviewer ______ Date ______ Notes: ____________________________

## B01 — ORIGINAL baseline: What are the differences between CSF 1.1 and 2.0 for supply chain risk management?
- **Claims to verify (the false ones included):** (1) CSF 1.1 has "two subcategories: ID.SC-1 and ID.SC-2"; (2) CSF 1.1 "only had subcategories under the Identify function"; (3) GV.SC-01 through GV.SC-10 exist in CSF 2.0 (only 7 were in the evidence); (4) the crosswalk "maps these new subcategories back to the two CSF 1.1 subcategories".
- **Sources:** CSF 1.1 category ID.SC and ID.SC-1…5 — `nist_csf_1_1.pdf` p.35 [28] (ID.SC-5 on p.36 [29]); CSF 2.0 GV.SC — `nist_csf_2_0.pdf` p.22–23; crosswalk rows 22 (GV.SC→ID.SC), 23–34 (GV.SC-01…10), 28 (→ID.SC-3), 31 (→ID.SC-4), 32 (→ID.SC-5); GV.RM-05 and ID.RA-10 (cited in the answer).
- **Preliminary [AI]:** partly incorrect; low completeness; retrieval failure (row 22, ID.SC-3/4/5 absent) plus generation overreach. [M] fails `expected_rows_covered` (row 22). [J] unavailable (two failed judge attempts; one partial batch only).
- **Disputed / unsupported:** claims (1)–(4) above. Not fully correct or complete.
- ☐ CSF 1.1 has five ID.SC subcategories (confirm)  ☐ Row 22 exists as stated  ☐ "Two subcategories" is false  ☐ Overall: incorrect / partly correct (circle)
- Reviewer ______ Date ______ Notes: ____________________________

## B01 — FINAL repair (post-hoc; verify separately, never merge with the baseline)
- **Claims to verify:** ID.SC-1…5 enumerated; Identify→Govern move (row 22); GV.SC-06 "planning and due diligence before relationships", GV.SC-09 life-cycle monitoring, GV.SC-10 post-agreement provisions; the 10 listed mappings (rows 22, 23, 25, 26, 27, 28, 29, 30, 33, 34); the stated GV.SC-03 conflict (rows 25, 26).
- **Sources:** same as above plus `nist_csf_2_0.pdf` p.23 [18] for GV.SC-06.
- **Preliminary [AI]:** false "two" claim gone; row 22 present; **not** fully correct or complete — (a) never explains what ID.SC-3/4/5 cover although their definitions were supplied and cited; (b) calls GV.SC-06/-03/-10 "new concepts"/"introduces" while mapping them to ID.SC-1/-2 (rows 29, 25, 34) — possibly overstated novelty; (c) omits rows 24, 31, 32 and rows mapping other categories into ID.SC (disclosed). [M] all applicable checks pass; serialized evidence 11,963 ≤ 12,000. [J] none.
- ☐ Mappings correct  ☐ Identify→Govern statement correct  ☐ Novelty framing acceptable / overstated (circle)  ☐ Gap (a) is acceptable for now  ☐ Disagree
- Reviewer ______ Date ______ Notes: ____________________________

## C01 — How does GV.OC-01 map to CSF 1.1?
- **Claims to verify:** GV.OC-01 maps to ID.BE-2 (row 4) and ID.BE-3 (row 5).
- **Sources:** crosswalk rows 4 and 5; `nist_csf_2_0.pdf` p.21 [16] (GV.OC-01); `nist_csf_1_1.pdf` p.32 [25] (ID.BE-2, ID.BE-3).
- **Preliminary [AI]:** correct, faithful, complete; rows 4/5 support the mapping claims. [M] pass. [J] 5/5/5/5 and citation support 2/5.
- **Disputed:** only the citation-support score (per-citation reading: three supplementary definition chunks counted as not supporting the mapping alone). Not ruled on.
- ☐ Correct  ☐ Faithful  ☐ Complete  ☐ Citation supports claim (claim-level)  ☐ Citation supports (per-citation)  ☐ Relevant
- Reviewer ______ Date ______ Notes: ____________________________

## F01 — How does GV.SC-03 map to CSF 1.1?
- **Claims to verify:** the workbook has BOTH row 25 (GV.SC-03→ID.SC-2, mapped) and row 26 (GV.SC-03, new_in_2_0, "Conceptually new in 2.0"); the answer reports both and picks neither.
- **Sources:** crosswalk rows 25, 26; `nist_csf_2_0.pdf` p.22 [17]; `nist_csf_1_1.pdf` p.35 [28] (ID.SC-2).
- **Preliminary [AI]:** correct, conflict preserved, complete. [M] pass. [J] 5/5/5/5, citation support 3/5 (two supplementary chunks counted as non-supporting). Minor wording: "as per pipeline findings" is an internal term.
- ☐ Correct  ☐ Faithful  ☐ Complete  ☐ Conflict preserved  ☐ Citation supports (claim-level)  ☐ (per-citation)  ☐ Relevant
- Reviewer ______ Date ______ Notes: ____________________________

## E01 — How does GV.OV-01 map to CSF 1.1?
- **Claims to verify:** the answer says GV.OV-01 "does not map to any CSF 1.1 element", "no direct equivalent in CSF 1.1".
- **Sources:** crosswalk row 46 (GV.OV-01, new_in_2_0, "Conceptually new in 2.0", no reference); `nist_csf_2_0.pdf` p.22 [17].
- **What the workbook establishes:** GV.OV-01 is *conceptually new in CSF 2.0* and *no CSF 1.1 reference is listed*. "No direct equivalent exists" is a stronger semantic statement than that.
- **Preliminary [AI]:** correct on the official record; wording stronger than the source. [M] pass. [J] 5/5/5/5, citation support 4/5.
- ☐ Correct  ☐ Faithful  ☐ Stronger wording acceptable / should be softened (circle)  ☐ Complete  ☐ Citation supports (claim-level)  ☐ (per-citation)
- Reviewer ______ Date ______ Notes: ____________________________

## H02 — Which CSF control requires quantum-safe cryptography?
- **Claims to verify:** abstention was appropriate; the stated reason (no reference to quantum-safe cryptography in the supplied evidence) is accurate.
- **Sources:** whole CSF 1.1 and 2.0 PDFs and workbook: search for quantum / post-quantum / cryptograph / encrypt. Retrieved evidence was access-control records (PR.AC-2, -6, -7), `nist_csf_1_1.pdf` p.36 [29] etc.
- **Preliminary [AI]:** abstention appropriate for the available evidence. The stored corpus has zero matches for those terms, but a zero-match search is not proof that a concept cannot exist anywhere. [M] abstention check passes. [J] not judged (abstention).
- **Limitations (not major failures):** the `uncertainties` aside naming PR.DS/PR.PT categories and the Protect function came from model background knowledge, not the supplied evidence; retrieval returned off-topic access-control records.
- ☐ Abstention appropriate  ☐ Reason accurate  ☐ Zero-match claim holds in the original PDFs  ☐ Out-of-evidence aside acceptable  ☐ Disagree
- Reviewer ______ Date ______ Notes: ____________________________

---
## Gold expectations vs official source records
Values below are what the stored (ingested) records say; an AI assistant also read the original files directly (see packet) and found them consistent, but **a human has not**. **Data distinction.** The original workbook (`nist_csf_transition.xlsx`, sheet `Relationships`) has only these columns: Focal Document Element, Focal Document Element Description, Reference Document Element, Reference Document Element Description, Comments (Optional), Strength of Relationship (Optional). The `mapped`/`new_in_2_0` labels below are ControlShift-derived. Gold file: `eval/answer_questions.jsonl` (AI-curated, unreviewed).

| Q | Gold expectation | Stored official record | Check against original |
|---|---|---|---|
| A01 | GV.SC-03 integrates supply chain risk management into broader risk processes | CSF 2.0 GV.SC-03 text (p.22): "Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes" | ☐ matches PDF |
| B01 | official row 22: GV.SC → ID.SC (the only expected row) | row 22, sheet Relationships: GV.SC → ID.SC, `mapped`, no comment | ☐ matches xlsx |
| C01 | row 4: GV.OC-01 → ID.BE-2; row 5: GV.OC-01 → ID.BE-3 | rows 4 and 5 as stated, `mapped` | ☐ rows 4, 5 match xlsx |
| F01 | row 25: GV.SC-03 → ID.SC-2; row 26: GV.SC-03 → none (conceptually new) | row 25 `mapped` → ID.SC-2; row 26 `new_in_2_0`, comment "Conceptually new in 2.0", no reference | ☐ rows 25, 26 match xlsx |
| E01 | row 46: GV.OV-01 → none (conceptually new in 2.0) | row 46 `new_in_2_0`, comment "Conceptually new in 2.0", no reference | ☐ row 46 matches xlsx |
| H02 | must abstain: topic absent (terms: quantum, post-quantum, cryptograph, encrypt, crypto) | 0 stored chunks contain those terms | ☐ confirmed in PDFs |

**Known gap in the gold set:** B01 expects only row 22. Passing that check does not make the comparison correct (ID.SC-3/4/5 and their rows 28/31/32 are not expected), so human reading of B01 matters more than its deterministic result.

## Sign-off (leave blank until reviewed)
Overall: ☐ All six reviewed  ☐ Disagreements recorded above  ☐ OK to finalize `eval/final_evaluation_draft.md` as the evaluation report
Reviewer: ______________________  Date: ______________
