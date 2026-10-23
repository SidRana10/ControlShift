# Human review packet — six live RAG answers (AI-assisted preliminary reviews; human sign-off NOT performed)

> **Status: DRAFT. Every assessment here is an AI-assisted preliminary reading of the saved answer against the evidence that was supplied and the stored
> official NIST CSF 1.1 / 2.0 text and crosswalk records. None of it is an independent human review, and no human sign-off exists.** Each section ends with
> `Human confirmation: PENDING`. Labels: **[M]** machine verification (deterministic code), **[J]** LLM-judge assessment (GPT-OSS), **[AI]** AI-assisted source review (my preliminary reading), **[H]** developer/human confirmation — **none has been given yet**.
> Six questions are a small exploratory sample and say nothing about general accuracy.

**Citation methodology (two separate concepts).** *Claim-level evidence support* and *per-citation precision* are different things; scores below keep the judge's numbers unchanged.

**Data distinction.** The original workbook (`nist_csf_transition.xlsx`, sheet `Relationships`) has only these columns: Focal Document Element, Focal Document Element Description, Reference Document Element, Reference Document Element Description, Comments (Optional), Strength of Relationship (Optional). It has **no `mapping_type` column**. The labels `mapped` / `new_in_2_0` used in ControlShift's database, checks and reports are **ControlShift-derived classifications** (`src/controlshift/ingest/crosswalk.py`): `mapped` when a reference element is present; `new_in_2_0` when there is no reference element and the comment contains "new" (here "Conceptually new in 2.0"). "Excel row" numbers are the sheet's row numbers (row 1 is the header).

**Original-source check (AI-assisted, performed programmatically).** The original files in `data/raw/` were read directly (not via the database): the workbook rows 4, 5, 22, 25, 26, 28, 31, 32 and 46 were read with openpyxl and the PDFs with PyMuPDF. Findings: rows 4/5 = GV.OC-01→ID.BE-2/ID.BE-3; row 22 = GV.SC→ID.SC; row 25 = GV.SC-03→ID.SC-2; row 26 = GV.SC-03, no reference, comment "Conceptually new in 2.0"; rows 28/31/32 = GV.SC-05→ID.SC-3, GV.SC-07→ID.SC-4, GV.SC-08→ID.SC-5; row 46 = GV.OV-01, no reference, "Conceptually new in 2.0". CSF 1.1 PDF: ID.SC-1…ID.SC-5 are all present (pp.35–36) with the definitions quoted in the packet. CSF 2.0 PDF: GV.SC-03 (p.22), GV.OV-01 (p.22), GV.OC-01 (p.21) present with the quoted text. Literal search of both PDFs and the workbook text for "quantum", "post-quantum", "cryptograph", "encrypt", "crypto": 0 matches. This was done by an AI assistant; **no independent human has completed the checklist**, and no reviewer sign-off or date exists.

**Citation-support methodology (detail).** Two different questions are easy to blur:
- *Claim-level support* — does an authoritative citation support the factual claim? (For a mapping claim, the official crosswalk row does.)
- *Per-citation precision* — does EACH attached citation, on its own, support the claim it is attached to? (A supplementary definition chunk for a mapped control does not by itself establish the mapping.)

My [AI] reading is claim-level; GPT-OSS's score [J] looks per-citation (it listed supplementary chunks as "does not support", which is a per-citation-precision judgement). GPT-OSS's scores are reported unchanged (A01 5/5, C01 2/5, F01 3/5, E01 4/5). The gap may come from the stricter per-citation reading; neither reading is declared right or wrong until a human confirms which one the rubric intends.

**How to review:** for each question read the answer, check each statement against the cited excerpt (and the NIST source if in doubt), then record: factual correctness,
faithfulness to the evidence, completeness, citation support and relevance (1–5 or Pass/Partial/Fail, your choice) in `eval/judge_calibration.json` or here.

**B01 note:** the six-question baseline uses the ORIGINAL B01 answer. The two later B01 retests are post-hoc repair results (section "B01 — post-hoc repair") and must not replace the baseline.

## Overview of preliminary findings
| Q | Answer | [M] deterministic | [AI] correctness | [AI] faithfulness | [AI] completeness | [AI] citations | Failure type |
|---|---|---|---|---|---|---|---|
| A01 | answered | all pass | correct | faithful | complete | support | none |
| B01 (original) | answered | **1 fail** (row 22) | **partly incorrect** | partly (unsupported "two"/"only") | low | mostly relevant | **retrieval** (row 22, ID.SC-3/4/5 absent) **+ generation** overreach |
| C01 | answered | all pass | correct | faithful | complete | support | none |
| F01 | answered | all pass | correct | faithful | complete | support | none |
| E01 | answered | all pass | correct | faithful (one mild extrapolation) | complete | support | none |
| H02 | abstained | all pass | correct abstention | faithful, one out-of-evidence aside | n/a | n/a | none (retrieval noise only) |

---

## A01 — exact control

**Question:** What does GV.SC-03 require?

**Category:** exact_control  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** answered

### Actual answer
In NIST CSF 2.0, GV.SC-03 requires that cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes.

**Key changes:**
- GV.SC-03 (CSF 2.0) mandates the integration of cybersecurity supply chain risk management into broader organizational risk management, assessment, and improvement processes. `chunk:csf2.0:subcategory:GV.SC-03`

**Answer-level citations:** `chunk:csf2.0:subcategory:GV.SC-03`

### Key supporting source excerpts (exact text supplied to the generator)
- `chunk:csf2.0:subcategory:GV.SC-03`: GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes

### Expected (existing gold dataset)
- Expected facts: GV.SC-03 integrates supply chain risk management into broader risk processes. [chunk:csf2.0:subcategory:GV.SC-03]

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS; mapping_pairs_official=PASS; mapping_cites_matching_row=PASS; versions_correct=PASS; expected_controls_referenced=PASS; no_unsupported_removal=PASS; no_uncited_claims=PASS (n/a: expected_rows_covered, conflict_preserved, new_control_no_reference, no_forbidden_mappings)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Correctness: correct — the official GV.SC-03 text is the integration outcome quoted. Faithfulness: faithful; "mandates" is looser than the source — GV.SC-03 is an outcome statement in a voluntary framework ("is integrated into …"), not a legal mandate — and "broader organizational" is light paraphrase of "is integrated into … enterprise risk management". Completeness: complete for the single expected fact. Citations: the one cited chunk is the GV.SC-03 record and supports both statements. Relevance: direct.

### Specific issues
- Judge citation support [J] 5/5 (unchanged): one citation, which supports the claim at both levels.
- Wording: "requires"/"mandates" should not be read as a legal mandate; NIST describes desired outcomes. Otherwise none material. Four unused sibling subcategories (GV.SC-01/02/08/10) were retrieved alongside; harmless.

**Failure attribution:** none

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## B01 — cross-version comparison — ORIGINAL BASELINE

**Question:** What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

**Category:** comparison  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** answered

### Actual answer
In CSF 1.1, supply chain risk management is primarily addressed under the Identify function with two subcategories: ID.SC-1 (processes identified and established) and ID.SC-2 (suppliers identified, prioritized, and assessed). In CSF 2.0, this focus is significantly expanded and restructured. A new category, Cybersecurity Supply Chain Risk Management (GV.SC), is introduced under the Govern function, containing multiple subcategories (GV.SC-01 through GV.SC-10) that cover program establishment, integration with enterprise risk management, supplier prioritization, due diligence, lifecycle monitoring, and post-contract activities. Additionally, CSF 2.0 includes GV.RM-05 for communication lines regarding supplier risks and ID.RA-10 for assessing critical suppliers prior to acquisition. The official crosswalk maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories, indicating a shift from a limited identification focus to a comprehensive governance and lifecycle management approach.

**Key changes:**
- CSF 2.0 introduces a dedicated 'Cybersecurity Supply Chain Risk Management' category (GV.SC) under the Govern function, whereas CSF 1.1 only had subcategories under the Identify function (ID.SC). `chunk:csf2.0:text:65a38d02bf94, chunk:csf1.1:subcategory:ID.SC-1, chunk:csf1.1:subcategory:ID.SC-2`
- CSF 2.0 expands the scope to include specific governance activities such as establishing a program/strategy (GV.SC-01), integrating with enterprise risk management (GV.SC-03, GV.SC-09), performing due diligence before relationships (GV.SC-06), and planning for post-contract activities (GV.SC-10), which are not explicitly detailed as separate subcategories in CSF 1.1. `chunk:csf2.0:subcategory:GV.SC-01, chunk:csf2.0:subcategory:GV.SC-03, chunk:csf2.0:subcategory:GV.SC-06, chunk:csf2.0:subcategory:GV.SC-09, chunk:csf2.0:subcategory:GV.SC-10`
- CSF 2.0 adds specific requirements for assessing critical suppliers prior to acquisition (ID.RA-10) and establishing lines of communication for supplier risks (GV.RM-05). `chunk:csf2.0:subcategory:ID.RA-10, chunk:csf2.0:subcategory:GV.RM-05`

**Mappings:**
- GV.RM-05 → ID.SC-1 — Official crosswalk maps GV.RM-05 to ID.SC-1. `xwalk:row19`
- GV.SC-01 → ID.SC-1 — Official crosswalk maps GV.SC-01 to ID.SC-1. `xwalk:row23`
- GV.SC-03 → ID.SC-2 — Official crosswalk maps GV.SC-03 to ID.SC-2. `xwalk:row25`
- GV.SC-04 → ID.SC-2 — Official crosswalk maps GV.SC-04 to ID.SC-2. `xwalk:row27`
- GV.SC-06 → ID.SC-1 — Official crosswalk maps GV.SC-06 to ID.SC-1. `xwalk:row29`
- GV.SC-07 → ID.SC-2 — Official crosswalk maps GV.SC-07 to ID.SC-2. `xwalk:row30`
- GV.SC-09 → ID.SC-1 — Official crosswalk maps GV.SC-09 to ID.SC-1. `xwalk:row33`
- GV.SC-10 → ID.SC-1 — Official crosswalk maps GV.SC-10 to ID.SC-1. `xwalk:row34`
- ID.RA-10 → ID.SC-2 — Official crosswalk maps ID.RA-10 to ID.SC-2. `xwalk:row77`

**Uncertainties stated:**
- The evidence does not provide a complete list of all CSF 2.0 subcategories under GV.SC, only specific ones (01, 03, 04, 06, 07, 09, 10).
- The evidence does not explicitly state if any CSF 1.1 supply chain controls were removed, only that they were mapped to new CSF 2.0 controls.

**Unresolved questions stated:**
- What are the specific descriptions of the missing GV.SC subcategories (e.g., GV.SC-02, GV.SC-05, GV.SC-08) in CSF 2.0?

**Answer-level citations:** `chunk:csf1.1:subcategory:ID.SC-1`, `chunk:csf1.1:subcategory:ID.SC-2`, `chunk:csf2.0:subcategory:GV.RM-05`, `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-04`, `chunk:csf2.0:subcategory:GV.SC-06`, `chunk:csf2.0:subcategory:GV.SC-07`, `chunk:csf2.0:subcategory:GV.SC-09`, `chunk:csf2.0:subcategory:GV.SC-10`, `chunk:csf2.0:subcategory:ID.RA-10`, `chunk:csf2.0:text:65a38d02bf94`, `xwalk:row19`, `xwalk:row23`, `xwalk:row25`, `xwalk:row27`, `xwalk:row29`, `xwalk:row30`, `xwalk:row33`, `xwalk:row34`, `xwalk:row77`

### Key supporting source excerpts (exact text supplied to the generator)
- `chunk:csf1.1:subcategory:ID.SC-1`: ID.SC-1: Cyber supply chain risk management processes are identified, established, assessed, managed, and agreed to by organizational stakeholders
- `chunk:csf1.1:subcategory:ID.SC-2`: ID.SC-2: Suppliers and third party partners of information systems, components, and services are identified, prioritized, and assessed using a cyber supply chain risk assessment process
- `chunk:csf2.0:subcategory:GV.SC-01`: GV.SC-01: A cybersecurity supply chain risk management program, strategy, objectives, policies, and processes are established and agreed to by organizational stakeholders
- `chunk:csf2.0:subcategory:GV.SC-06`: GV.SC-06: Planning and due diligence are performed to reduce risks before entering into formal supplier or other third-party relationships
- `chunk:csf2.0:subcategory:GV.RM-05`: GV.RM-05: Lines of communication across the organization are established for cybersecurity risks, including risks from suppliers and other third parties
- `chunk:csf2.0:subcategory:ID.RA-10`: ID.RA-10: Critical suppliers are assessed prior to acquisition
- `xwalk:row25`: Official crosswalk row 25: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 ID.SC-2 (Suppliers and third party partners of information systems, components, and services are identified, prioritized,…

### Expected (existing gold dataset)
- Expected facts: Official row 22: GV.SC -> ID.SC [xwalk:row22]
- Expected crosswalk rows: [22]

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS; mapping_pairs_official=PASS; mapping_cites_matching_row=PASS; versions_correct=PASS; no_unsupported_removal=PASS; no_uncited_claims=PASS; **expected_rows_covered=FAIL** (official rows not cited: [22]) (n/a: expected_controls_referenced, conflict_preserved, new_control_no_reference, no_forbidden_mappings)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Source facts (stored official records): CSF 1.1 category **ID.SC** has FIVE subcategories — ID.SC-3 (contracts implement measures), ID.SC-4 (suppliers routinely assessed against contractual obligations), ID.SC-5 (response and recovery planning/testing with suppliers) in addition to the two shown; CSF 2.0 GV.SC has ten; official row 22 maps the categories GV.SC → ID.SC. Correctness: **partly incorrect** (see issues). Faithfulness: the individual definitions it quotes (ID.SC-1, ID.SC-2, GV.RM-05, ID.RA-10, GV.SC-xx) match the supplied text, but two statements go beyond the evidence. Completeness: **low** — no category-level mapping, three of five 1.1 subcategories missing, only 7 of 10 GV.SC subcategories supplied. Citations: relevant records are cited; key change 1 cites a narrative chunk (the Core appendix with the category table) for the existence of GV.SC — plausible [H]. Relevance: on topic.

### Specific issues
- **False:** "two subcategories: ID.SC-1 … and ID.SC-2" — CSF 1.1 has five. Also "CSF 1.1 only had subcategories under the Identify function (ID.SC)" misdescribes ID.SC (a category with five subcategories).
- **Unsupported by the evidence it was given:** "GV.SC-01 through GV.SC-10" (evidence held 7 of 10; the model itself listed GV.SC-02/05/08 as missing in `uncertainties`).
- **Internally inconsistent:** calls the GV.SC subcategories "new" yet says the crosswalk "maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories" — the crosswalk maps them to ID.SC-1 … ID.SC-5 and to other 1.1 categories.
- Omits official row 22 (deterministic fail) and rows 28/31/32 (ID.SC-3/4/5).

**Failure attribution:** **Retrieval failure** (row 22 and ID.SC-3/4/5 never reached the model; confirmed: they exist in the database and index) **plus a generation failure** (asserting "two"/"only" from an excerpt, which the later prompt rule targets).

**Status:** the six-question baseline B01 is this ORIGINAL answer; it is **not** fully correct or complete.

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## C01 — official mapping

**Question:** How does GV.OC-01 map to CSF 1.1?

**Category:** official_mapping  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** answered

### Actual answer
According to the official crosswalk, the CSF 2.0 subcategory GV.OC-01 maps to two CSF 1.1 subcategories: ID.BE-2 and ID.BE-3.

**Key changes:**
- GV.OC-01 (CSF 2.0) is mapped to ID.BE-2 (CSF 1.1). `xwalk:row4`
- GV.OC-01 (CSF 2.0) is mapped to ID.BE-3 (CSF 1.1). `xwalk:row5`

**Mappings:**
- GV.OC-01 → ID.BE-2 — Official crosswalk mapping from CSF 2.0 to CSF 1.1. `xwalk:row4`
- GV.OC-01 → ID.BE-3 — Official crosswalk mapping from CSF 2.0 to CSF 1.1. `xwalk:row5`

**Answer-level citations:** `xwalk:row4`, `xwalk:row5`, `chunk:csf2.0:subcategory:GV.OC-01`, `chunk:csf1.1:subcategory:ID.BE-2`, `chunk:csf1.1:subcategory:ID.BE-3`

### Key supporting source excerpts (exact text supplied to the generator)
- `xwalk:row4`: Official crosswalk row 4: CSF 2.0 GV.OC-01 (The organizational mission is understood and informs cybersecurity risk management) -> CSF 1.1 ID.BE-2 (The organization’s place in critical infrastructure and its industry sector is identified and communicated); mapping_type=mapped; comments=
- `xwalk:row5`: Official crosswalk row 5: CSF 2.0 GV.OC-01 (The organizational mission is understood and informs cybersecurity risk management) -> CSF 1.1 ID.BE-3 (Priorities for organizational mission, objectives, and activities are established and communicated); mapping_type=mapped; comments=
- `chunk:csf2.0:subcategory:GV.OC-01`: GV.OC-01: The organizational mission is understood and informs cybersecurity risk management

### Expected (existing gold dataset)
- Expected facts: Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]; Official row 5: GV.OC-01 -> ID.BE-3 [xwalk:row5]
- Expected crosswalk rows: [4, 5]

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS; mapping_pairs_official=PASS; mapping_cites_matching_row=PASS; versions_correct=PASS; expected_rows_covered=PASS; expected_controls_referenced=PASS; no_unsupported_removal=PASS; no_uncited_claims=PASS (n/a: conflict_preserved, new_control_no_reference, no_forbidden_mappings)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Correctness: correct — official rows 4 and 5 are GV.OC-01 → ID.BE-2 and GV.OC-01 → ID.BE-3 (verified in the stored crosswalk). Faithfulness: faithful; the answer restates the rows. Completeness: complete (both expected rows; it does not say the mapping is one-to-many in meaning, which was not asked). Citations: each mapping cites its own row. Relevance: direct.

### Specific issues
- Judge citation support [J] 2/5 (unchanged). Claim-level [AI]: rows 4 and 5 support the two mapping claims. Per-citation precision [J]: the three supplementary definition chunks (GV.OC-01, ID.BE-2, ID.BE-3) were counted as not supporting the mapping on their own. Possible strict per-citation reading; **not** ruled on.
- None material. The answer gives no description of what the mapping means (not required).

**Failure attribution:** none

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## F01 — conflicting official records

**Question:** How does GV.SC-03 map to CSF 1.1?

**Category:** conflict  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** answered

### Actual answer
According to the official crosswalk, CSF 2.0 subcategory GV.SC-03 maps to CSF 1.1 subcategory ID.SC-2. However, the official workbook also contains a separate entry indicating that GV.SC-03 is 'conceptually new in 2.0' with no corresponding CSF 1.1 reference. Both entries are present in the official records.

**Key changes:**
- CSF 2.0 GV.SC-03 is mapped to CSF 1.1 ID.SC-2 in the official crosswalk. `xwalk:row25`
- CSF 2.0 GV.SC-03 is also listed as 'conceptually new in 2.0' with no CSF 1.1 reference in the official crosswalk. `xwalk:row26`

**Mappings:**
- GV.SC-03 → ID.SC-2 — Official crosswalk row 25 maps GV.SC-03 to ID.SC-2. `xwalk:row25`
- GV.SC-03 → (no CSF 1.1 reference) — Official crosswalk row 26 lists GV.SC-03 as 'new_in_2_0' with the comment 'Conceptually new in 2.0' and no reference ID. `xwalk:row26`

**Uncertainties stated:**
- The official crosswalk contains conflicting entries for GV.SC-03: one mapping it to ID.SC-2 and another marking it as conceptually new in 2.0 with no 1.1 reference. Both are reported as per pipeline findings.

**Answer-level citations:** `xwalk:row25`, `xwalk:row26`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf1.1:subcategory:ID.SC-2`

### Key supporting source excerpts (exact text supplied to the generator)
- `xwalk:row25`: Official crosswalk row 25: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 ID.SC-2 (Suppliers and third party partners of information systems, components, and services are identified, prioritized,…
- `xwalk:row26`: Official crosswalk row 26: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 NO REFERENCE (); mapping_type=new_in_2_0; comments=Conceptually new in 2.0

### Expected (existing gold dataset)
- Expected facts: Official row 25: GV.SC-03 -> ID.SC-2 [xwalk:row25]; Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]
- Expected crosswalk rows: [25, 26]

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS; mapping_pairs_official=PASS; mapping_cites_matching_row=PASS; versions_correct=PASS; expected_rows_covered=PASS; expected_controls_referenced=PASS; conflict_preserved=PASS; no_unsupported_removal=PASS; no_uncited_claims=PASS (n/a: new_control_no_reference, no_forbidden_mappings)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Correctness: correct — the workbook holds BOTH row 25 (GV.SC-03 → ID.SC-2, mapped) and row 26 (GV.SC-03, new_in_2_0, "Conceptually new in 2.0"); verified. Faithfulness: faithful; it neither picks one nor invents a reconciliation. This is best described as an apparent inconsistency / dual-entry ambiguity in the workbook — not a definitively proven NIST error; ControlShift reports both entries. Completeness: complete. Citations: rows cited for their own claims. Relevance: direct.

### Specific issues
- Judge citation support [J] 3/5 (unchanged). Claim-level [AI]: rows 25 and 26 support their claims. Per-citation precision [J]: two of four attached citations (the supplementary GV.SC-03 / ID.SC-2 chunks) were counted as not supporting the mapping on their own. **Not** ruled on.
- Minor wording: "as per pipeline findings" refers to the application's internals, which a user would not know.

**Failure attribution:** none

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## E01 — conceptually new control

**Question:** How does GV.OV-01 map to CSF 1.1?

**Category:** conceptually_new  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** answered

### Actual answer
GV.OV-01 does not map to any CSF 1.1 element. The official crosswalk identifies GV.OV-01 as 'new_in_2_0' with the comment 'Conceptually new in 2.0', indicating there is no corresponding CSF 1.1 reference element.

**Key changes:**
- GV.OV-01 is a new subcategory in CSF 2.0 with no direct equivalent in CSF 1.1. `xwalk:row46`

**Mappings:**
- GV.OV-01 → (no CSF 1.1 reference) — Official crosswalk marks this element as conceptually new in CSF 2.0 with no CSF 1.1 reference. `xwalk:row46`

**Answer-level citations:** `xwalk:row46`, `chunk:csf2.0:subcategory:GV.OV-01`

### Key supporting source excerpts (exact text supplied to the generator)
- `xwalk:row46`: Official crosswalk row 46: CSF 2.0 GV.OV-01 (Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction) -> CSF 1.1 NO REFERENCE (); mapping_type=new_in_2_0; comments=Conceptually new in 2.0
- `chunk:csf2.0:subcategory:GV.OV-01`: GV.OV-01: Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction

### Expected (existing gold dataset)
- Expected facts: Official row 46: GV.OV-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row46]
- Expected crosswalk rows: [46]

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS; mapping_pairs_official=PASS; mapping_cites_matching_row=PASS; versions_correct=PASS; expected_rows_covered=PASS; expected_controls_referenced=PASS; new_control_no_reference=PASS; no_unsupported_removal=PASS; no_uncited_claims=PASS (n/a: conflict_preserved, no_forbidden_mappings)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Correctness: correct — row 46 marks GV.OV-01 new_in_2_0 ("Conceptually new in 2.0") with no CSF 1.1 reference; verified. Faithfulness: faithful, with one mild extrapolation: "no direct equivalent in CSF 1.1" restates "no reference" slightly more strongly than the workbook does. Completeness: complete. Citations: support. Relevance: direct.

### Specific issues
- Judge citation support [J] 4/5 (unchanged). Claim-level [AI]: row 46 supports the claim. Per-citation precision [J]: the GV.OV-01 definition chunk does not establish the mapping status by itself. **Not** ruled on.
- **Wording stronger than the source.** The official workbook (row 46) says only that GV.OV-01 is *conceptually new in CSF 2.0* with *no CSF 1.1 reference listed*. "No direct equivalent exists in CSF 1.1" (key change) and "does not map to any CSF 1.1 element" are stronger semantic statements than the workbook establishes: the workbook lists no mapping; it does not say that no related 1.1 content exists. [AI] preliminary; [H] to decide whether acceptable.

**Failure attribution:** none

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## H02 — unsupported question — abstention

**Question:** Which CSF control requires quantum-safe cryptography?

**Category:** abstention  **Generator:** Groq `qwen/qwen3.8-27b`  **Answer status:** abstained

### Actual answer
**ABSTAINED.** The provided evidence does not contain any CSF control that requires quantum-safe cryptography. The available passages describe general framework purposes, authentication, and identity management, but do not mention quantum-safe cryptography.
Reason given: The supplied evidence does not contain any reference to quantum-safe cryptography or any control requiring it.

**Uncertainties stated:**
- The evidence provided is limited to general descriptions of CSF 1.1 and 2.0 and specific access control subcategories (PR.AC-2, PR.AC-6, PR.AC-7). It does not include the full text of the CSF Core or specific cryptographic controls (such as those in the PR.DS or PR.PT categories in CSF 1.1 or the Protect function in CSF 2.0) where such requirements might be located.

**Unresolved questions stated:**
- Does any specific subcategory in CSF 1.1 or CSF 2.0 explicitly mandate quantum-safe cryptography?

**Answer-level citations:** none

### Key supporting source excerpts (exact text supplied to the generator)
- `chunk:csf1.1:category:PR.AC`: Identity Management, Authentication and Access Control (PR.AC): Access to physical and logical assets and associated facilities is limited to authorized users, processes, and devices, and is managed consistent with the assessed risk of unauthorized access to authorized activities and transactions.
- `chunk:csf1.1:subcategory:PR.AC-2`: PR.AC-2: Physical access to assets is managed and protected
- `chunk:csf1.1:subcategory:PR.AC-6`: PR.AC-6: Identities are proofed and bound to credentials and asserted in interactions
- `chunk:csf1.1:subcategory:PR.AC-7`: PR.AC-7: Users, devices, and other assets are authenticated (e.g., single-factor, multi-factor) commensurate with the risk of the transaction (e.g., individuals’ security and privacy risks and other organizational risks)

(Retrieved evidence was off-topic for the question: PR.AC access-control records and general framework text.)

### Expected (existing gold dataset)
- Must abstain (basis: topic_absent): The corpus has no cryptography content at all; any retrieved passage is off-topic.
- Expected facts: none

### Machine-checked [M]
schema_valid=PASS; citation_ids_valid=PASS; citations_in_bundle=PASS; abstention_correct=PASS (n/a: mapping_pairs_official, mapping_cites_matching_row, versions_correct, expected_rows_covered, expected_controls_referenced, conflict_preserved, new_control_no_reference, no_forbidden_mappings, no_unsupported_removal, no_uncited_claims)

### Preliminary assessment [AI-assisted, source-based — NOT a human review]
Correctness: the abstention was appropriate for the evidence available — a literal search of the stored corpus AND (separately, AI-assisted) of the original PDFs/workbook finds NO text containing "quantum", "cryptograph", "encrypt" or "crypto" (0 matches), so no CSF control in this corpus literally mentions it. That does not prove that no semantically related concept exists. Faithfulness: the stated reason and the description of the retrieved passages (access-control PR.AC-2/6/7, general framework text) match the evidence. Not scored with the normal answer-quality rubric (no claims to support). Relevance: it answers the question by declining.

### Specific issues
- *Limitation, not a major failure.* A zero-match keyword search of this stored corpus is not proof that a concept cannot appear anywhere (other documents, other wording); it only shows the supplied corpus has none, which is what the abstention rests on.
- *Limitation, not a major failure.* The `uncertainties` entry names PR.DS/PR.PT categories and "the Protect function" as places a cryptographic requirement "might be located" — that comes from the model's background knowledge, not from the evidence (the system rules forbid outside knowledge). Harmless here but worth noting [H].
- Retrieval returned access-control (PR.AC) controls for a cryptography question — semantic drift, no effect on the outcome.

**Failure attribution:** none (retrieval noise only)

**Human confirmation: PENDING** (reviewer: —, date: —)

---

## B01 — post-hoc repair (SEPARATE from the baseline above)

These results come from changing the pipeline after the failure was seen, then re-asking the same question once (Qwen, one request each). They are **repair checks, not benchmark results**, and they do not replace the original B01 baseline.

| | Original (baseline) | First repair | Final repair |
|---|---|---|---|
| [M] deterministic | 1 fail (row 22) | all pass | all pass |
| Serialized evidence | 11,940 chars | 12,138 (over 12,000) | 11,963 (≤ 12,000) |
| [AI] ID.SC-1…5 enumerated | no ("two") | via mappings only | yes |
| [AI] roles of ID.SC-3/4/5 explained | no | no | **no** |

**Final repaired answer** (`eval/live_runs/2026-10-22_B01_final_retest_budget_priority.json`):

In CSF 1.1, supply chain risk management is located in the Identify function under the category ID.SC, with specific subcategories ID.SC-1 through ID.SC-5. In CSF 2.0, this area is moved to the Govern function under the category GV.SC, with subcategories GV.SC-01 through GV.SC-10. The 2.0 version introduces a more granular set of controls, including new concepts such as planning and due diligence before entering relationships (GV.SC-06), integration into enterprise risk management (GV.SC-03), and provisions for post-contract activities (GV.SC-10). The official crosswalk maps the 2.0 category GV.SC to the 1.1 category ID.SC, and maps specific 2.0 subcategories to their 1.1 counterparts, though some 2.0 controls are marked as conceptually new.

**Key changes:**
- The category for supply chain risk management moved from Identify (ID.SC) in CSF 1.1 to Govern (GV.SC) in CSF 2.0. `chunk:csf1.1:category:ID.SC, chunk:csf2.0:category:GV.SC, xwalk:row22`
- CSF 2.0 introduces GV.SC-06, which requires planning and due diligence to reduce risks before entering into formal supplier relationships, a specific requirement not explicitly present as a standalone subcategory in the provided CSF 1.1 evidence. `chunk:csf2.0:subcategory:GV.SC-06, xwalk:row29`
- CSF 2.0 introduces GV.SC-10, which requires supply chain risk management plans to include provisions for activities after the conclusion of a partnership or service agreement. `chunk:csf2.0:subcategory:GV.SC-10, xwalk:row34`
- CSF 2.0 GV.SC-03 is mapped to CSF 1.1 ID.SC-2 but is also listed as 'new_in_2_0' with the comment 'Conceptually new in 2.0', indicating a conflict in the official workbook regarding its novelty. `xwalk:row25, xwalk:row26`
- CSF 2.0 GV.SC-09 emphasizes monitoring supply chain security practices throughout the technology product and service life cycle, mapped to CSF 1.1 ID.SC-1. `chunk:csf2.0:subcategory:GV.SC-09, xwalk:row33`

**Mappings:**
- GV.SC → ID.SC — Category level mapping from CSF 2.0 to CSF 1.1. `xwalk:row22`
- GV.SC-01 → ID.SC-1 — Mapped control. `xwalk:row23`
- GV.SC-03 → ID.SC-2 — Mapped control. Note: A separate row also lists this as new_in_2_0. `xwalk:row25`
- GV.SC-03 → (no CSF 1.1 reference) — Listed as conceptually new in 2.0 in a separate workbook row. `xwalk:row26`
- GV.SC-04 → ID.SC-2 — Mapped control. `xwalk:row27`
- GV.SC-05 → ID.SC-3 — Mapped control. `xwalk:row28`
- GV.SC-06 → ID.SC-1 — Mapped control. `xwalk:row29`
- GV.SC-07 → ID.SC-2 — Mapped control. `xwalk:row30`
- GV.SC-09 → ID.SC-1 — Mapped control. `xwalk:row33`
- GV.SC-10 → ID.SC-1 — Mapped control. `xwalk:row34`

**Uncertainties stated:**
- The evidence is an excerpt; some records (e.g., GV.SC-02, GV.SC-08, ID.SC-4, ID.SC-5) are present in the evidence blocks but their specific crosswalk mappings are not provided in the supplied xwalk rows, so their 1.1 counterparts are not listed in the mappings array.
- The official workbook contains conflicting entries for GV.SC-03, listing it as both mapped to ID.SC-2 and as new_in_2_0.
- Missing evidence indicates that some official records were omitted for context budget, so the coverage of the comparison may be incomplete.

**Unresolved questions stated:**
- What is the definitive status of GV.SC-03 in the official crosswalk, given the conflicting 'mapped' and 'new_in_2_0' entries?

**Answer-level citations:** `chunk:csf1.1:category:ID.SC`, `chunk:csf1.1:subcategory:ID.SC-1`, `chunk:csf1.1:subcategory:ID.SC-2`, `chunk:csf1.1:subcategory:ID.SC-3`, `chunk:csf1.1:subcategory:ID.SC-4`, `chunk:csf1.1:subcategory:ID.SC-5`, `chunk:csf2.0:category:GV.SC`, `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-02`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-04`, `chunk:csf2.0:subcategory:GV.SC-05`, `chunk:csf2.0:subcategory:GV.SC-06`, `chunk:csf2.0:subcategory:GV.SC-07`, `chunk:csf2.0:subcategory:GV.SC-08`, `chunk:csf2.0:subcategory:GV.SC-09`, `chunk:csf2.0:subcategory:GV.SC-10`, `xwalk:row22`, `xwalk:row23`, `xwalk:row25`, `xwalk:row26`, `xwalk:row27`, `xwalk:row28`, `xwalk:row29`, `xwalk:row30`, `xwalk:row33`, `xwalk:row34`

**Preliminary assessment [AI]:** the false "two subcategories" claim is gone; the five-subcategory enumeration, the Identify → Govern move, row 22 and the GV.SC-03 conflict (rows 25/26) are present and supported; all 10 mappings are official rows [M]. The answer states that some official records were left out for the context budget.
**Recorded status:** improved, **not** fully correct or complete. **Issues:** (1) it never says what ID.SC-3/4/5 cover although their definitions were supplied and cited; (2) it calls GV.SC-06, -03 and -10 "new concepts"/"introduces" while mapping them to ID.SC-1/ID.SC-2 (rows 29, 25, 34), which overstates novelty [H]; (3) "a more granular set of controls" is interpretation; (4) rows 24, 31, 32 and the rows mapping other categories into ID.SC did not fit the context (disclosed by the answer).
**Human confirmation: PENDING.**
