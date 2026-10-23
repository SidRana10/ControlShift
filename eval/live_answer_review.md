# Live RAG answer review (six-question exploratory sample)

Everything below was produced by the real ControlShift pipeline (hybrid retrieval -> evidence assembly -> Groq `qwen/qwen3.8-27b`). **Deterministic findings** (schema, citation ids, official crosswalk rows, versions, abstention) are machine-checked. **Semantic quality is NOT assessed here**: whether each statement is faithful to its cited text, and whether the answer is correct and complete, are `PENDING` human review. No accuracy, faithfulness or correctness score is given or implied; six questions are a small exploratory sample. LLM-judge output is not part of this report. **Data note:** the original crosswalk workbook has no `mapping_type` column; `mapped` / `new_in_2_0` are ControlShift-derived labels (reference present / no reference with a "new" comment). No independent human review has been performed.

| Question | Category | Answer status | Deterministic checks | Human review |
|---|---|---|---|---|
| A01 | exact_control | answered | all applicable passed | not performed |
| B01 | comparison | answered | FAILED: expected_rows_covered | not performed |
| C01 | official_mapping | answered | all applicable passed | not performed |
| F01 | conflict | answered | all applicable passed | not performed |
| E01 | conceptually_new | answered | all applicable passed | not performed |
| H02 | abstention | abstained | all applicable passed | not performed |

---

## A01 — exact_control

**Question:** What does GV.SC-03 require?

### Actual output

In NIST CSF 2.0, GV.SC-03 requires that cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes.

**Key changes**

- GV.SC-03 (CSF 2.0) mandates the integration of cybersecurity supply chain risk management into broader organizational risk management, assessment, and improvement processes. `chunk:csf2.0:subcategory:GV.SC-03`

**Answer-level citations:** `chunk:csf2.0:subcategory:GV.SC-03`

### Evidence supplied to the generator

5 items: `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-02`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-08`, `chunk:csf2.0:subcategory:GV.SC-10`

<details><summary>Cited evidence text</summary>

- `chunk:csf2.0:subcategory:GV.SC-03`: GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes

</details>

### Expected (existing gold dataset; never shown to the generator)

- Expected crosswalk rows: none
- Expected mappings: none
- Expected facts: GV.SC-03 integrates supply chain risk management into broader risk processes. [chunk:csf2.0:subcategory:GV.SC-03]

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | PASS |  |
| mapping_cites_matching_row | PASS |  |
| versions_correct | PASS |  |
| expected_rows_covered | N/A |  |
| expected_controls_referenced | PASS |  |
| conflict_preserved | N/A |  |
| new_control_no_reference | N/A |  |
| no_forbidden_mappings | N/A |  |
| no_unsupported_removal | PASS |  |
| no_uncited_claims | PASS |  |

### Needs human verification (semantic; NOT assessed by any check)

- `S1` In NIST CSF 2.0, GV.SC-03 requires that cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assess… — no citation attached to this sentence (check it against the answer-level citations)
- `K1` GV.SC-03 (CSF 2.0) mandates the integration of cybersecurity supply chain risk management into broader organizational risk management, assessment, and improvem… — cited: `chunk:csf2.0:subcategory:GV.SC-03`

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 1217 prompt + 203 output = 1420
- Latency: 4.08 s
- Attempts: 1; rejections: none; warnings: none
- Source artifact: `eval/live_runs/2026-10-22_six_question_qwen_gptoss_partial_stopped_at_B01.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)

---

## B01 — comparison

**Question:** What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

### Actual output

In CSF 1.1, supply chain risk management is primarily addressed under the Identify function with two subcategories: ID.SC-1 (processes identified and established) and ID.SC-2 (suppliers identified, prioritized, and assessed). In CSF 2.0, this focus is significantly expanded and restructured. A new category, Cybersecurity Supply Chain Risk Management (GV.SC), is introduced under the Govern function, containing multiple subcategories (GV.SC-01 through GV.SC-10) that cover program establishment, integration with enterprise risk management, supplier prioritization, due diligence, lifecycle monitoring, and post-contract activities. Additionally, CSF 2.0 includes GV.RM-05 for communication lines regarding supplier risks and ID.RA-10 for assessing critical suppliers prior to acquisition. The official crosswalk maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories, indicating a shift from a limited identification focus to a comprehensive governance and lifecycle management approach.

**Key changes**

- CSF 2.0 introduces a dedicated 'Cybersecurity Supply Chain Risk Management' category (GV.SC) under the Govern function, whereas CSF 1.1 only had subcategories under the Identify function (ID.SC). `chunk:csf2.0:text:65a38d02bf94, chunk:csf1.1:subcategory:ID.SC-1, chunk:csf1.1:subcategory:ID.SC-2`
- CSF 2.0 expands the scope to include specific governance activities such as establishing a program/strategy (GV.SC-01), integrating with enterprise risk management (GV.SC-03, GV.SC-09), performing due diligence before relationships (GV.SC-06), and planning for post-contract activities (GV.SC-10), which are not explicitly detailed as separate subcategories in CSF 1.1. `chunk:csf2.0:subcategory:GV.SC-01, chunk:csf2.0:subcategory:GV.SC-03, chunk:csf2.0:subcategory:GV.SC-06, chunk:csf2.0:subcategory:GV.SC-09, chunk:csf2.0:subcategory:GV.SC-10`
- CSF 2.0 adds specific requirements for assessing critical suppliers prior to acquisition (ID.RA-10) and establishing lines of communication for supplier risks (GV.RM-05). `chunk:csf2.0:subcategory:ID.RA-10, chunk:csf2.0:subcategory:GV.RM-05`

**Mappings**

- GV.RM-05 → ID.SC-1 — Official crosswalk maps GV.RM-05 to ID.SC-1. `xwalk:row19`
- GV.SC-01 → ID.SC-1 — Official crosswalk maps GV.SC-01 to ID.SC-1. `xwalk:row23`
- GV.SC-03 → ID.SC-2 — Official crosswalk maps GV.SC-03 to ID.SC-2. `xwalk:row25`
- GV.SC-04 → ID.SC-2 — Official crosswalk maps GV.SC-04 to ID.SC-2. `xwalk:row27`
- GV.SC-06 → ID.SC-1 — Official crosswalk maps GV.SC-06 to ID.SC-1. `xwalk:row29`
- GV.SC-07 → ID.SC-2 — Official crosswalk maps GV.SC-07 to ID.SC-2. `xwalk:row30`
- GV.SC-09 → ID.SC-1 — Official crosswalk maps GV.SC-09 to ID.SC-1. `xwalk:row33`
- GV.SC-10 → ID.SC-1 — Official crosswalk maps GV.SC-10 to ID.SC-1. `xwalk:row34`
- ID.RA-10 → ID.SC-2 — Official crosswalk maps ID.RA-10 to ID.SC-2. `xwalk:row77`

**Uncertainties stated by the answer**

- The evidence does not provide a complete list of all CSF 2.0 subcategories under GV.SC, only specific ones (01, 03, 04, 06, 07, 09, 10).
- The evidence does not explicitly state if any CSF 1.1 supply chain controls were removed, only that they were mapped to new CSF 2.0 controls.

**Unresolved questions**

- What are the specific descriptions of the missing GV.SC subcategories (e.g., GV.SC-02, GV.SC-05, GV.SC-08) in CSF 2.0?

**Answer-level citations:** `chunk:csf1.1:subcategory:ID.SC-1`, `chunk:csf1.1:subcategory:ID.SC-2`, `chunk:csf2.0:subcategory:GV.RM-05`, `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-04`, `chunk:csf2.0:subcategory:GV.SC-06`, `chunk:csf2.0:subcategory:GV.SC-07`, `chunk:csf2.0:subcategory:GV.SC-09`, `chunk:csf2.0:subcategory:GV.SC-10`, `chunk:csf2.0:subcategory:ID.RA-10`, `chunk:csf2.0:text:65a38d02bf94`, `xwalk:row19`, `xwalk:row23`, `xwalk:row25`, `xwalk:row27`, `xwalk:row29`, `xwalk:row30`, `xwalk:row33`, `xwalk:row34`, `xwalk:row77`

### Evidence supplied to the generator

24 items: `chunk:csf1.1:subcategory:ID.SC-1`, `chunk:csf1.1:subcategory:ID.SC-2`, `chunk:csf1.1:text:e2a14c45b7f5`, `chunk:csf2.0:subcategory:GV.OC-02`, `chunk:csf2.0:subcategory:GV.RM-05`, `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-04`, `chunk:csf2.0:subcategory:GV.SC-06`, `chunk:csf2.0:subcategory:GV.SC-07`, `chunk:csf2.0:subcategory:GV.SC-09`, `chunk:csf2.0:subcategory:GV.SC-10`, `chunk:csf2.0:subcategory:ID.RA-10`, `chunk:csf2.0:text:65a38d02bf94`, `xwalk:row19`, `xwalk:row23`, `xwalk:row25`, `xwalk:row27`, `xwalk:row29`, `xwalk:row30`, `xwalk:row33`, `xwalk:row34`, `xwalk:row6`, `xwalk:row77`

<details><summary>Cited evidence text</summary>

- `chunk:csf1.1:subcategory:ID.SC-1`: ID.SC-1: Cyber supply chain risk management processes are identified, established, assessed, managed, and agreed to by organizational stakeholders
- `chunk:csf1.1:subcategory:ID.SC-2`: ID.SC-2: Suppliers and third party partners of information systems, components, and services are identified, prioritized, and assessed using a cyber supply chain risk assessment process
- `chunk:csf2.0:subcategory:GV.RM-05`: GV.RM-05: Lines of communication across the organization are established for cybersecurity risks, including risks from suppliers and other third parties
- `chunk:csf2.0:subcategory:GV.SC-01`: GV.SC-01: A cybersecurity supply chain risk management program, strategy, objectives, policies, and processes are established and agreed to by organizational stakeholders
- `chunk:csf2.0:subcategory:GV.SC-03`: GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes
- `chunk:csf2.0:subcategory:GV.SC-04`: GV.SC-04: Suppliers are known and prioritized by criticality
- `chunk:csf2.0:subcategory:GV.SC-06`: GV.SC-06: Planning and due diligence are performed to reduce risks before entering into formal supplier or other third-party relationships
- `chunk:csf2.0:subcategory:GV.SC-07`: GV.SC-07: The risks posed by a supplier, their products and services, and other third parties are understood, recorded, prioritized, assessed, responded to, and monitored over the course of the relationship
- `chunk:csf2.0:subcategory:GV.SC-09`: GV.SC-09: Supply chain security practices are integrated into cybersecurity and enterprise risk management programs, and their performance is monitored throughout the technology product and service life cycle
- `chunk:csf2.0:subcategory:GV.SC-10`: GV.SC-10: Cybersecurity supply chain risk management plans include provisions for activities that occur after the conclusion of a partnership or service agreement
- `chunk:csf2.0:subcategory:ID.RA-10`: ID.RA-10: Critical suppliers are assessed prior to acquisition
- `chunk:csf2.0:text:65a38d02bf94`: This appendix describes the Functions, Categories, and Subcategories of the CSF Core. Table 1 lists the CSF 2.0 Core Function and Category names and unique alphabetic identifiers. Each Function name in the table is link…
- `xwalk:row19`: Official crosswalk row 19: CSF 2.0 GV.RM-05 (Lines of communication across the organization are established for cybersecurity risks, including risks from suppliers and other third parties) -> CSF 1.1 ID.SC-1 (Cyber supp…
- `xwalk:row23`: Official crosswalk row 23: CSF 2.0 GV.SC-01 (A cybersecurity supply chain risk management program, strategy, objectives, policies, and processes are established and agreed to by organizational stakeholders) -> CSF 1.1 I…
- `xwalk:row25`: Official crosswalk row 25: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 ID.SC-2 (Su…
- `xwalk:row27`: Official crosswalk row 27: CSF 2.0 GV.SC-04 (Suppliers are known and prioritized by criticality) -> CSF 1.1 ID.SC-2 (Suppliers and third party partners of information systems, components, and services are identified, pr…
- `xwalk:row29`: Official crosswalk row 29: CSF 2.0 GV.SC-06 (Planning and due diligence are performed to reduce risks before entering into formal supplier or other third-party relationships) -> CSF 1.1 ID.SC-1 (Cyber supply chain risk …
- `xwalk:row30`: Official crosswalk row 30: CSF 2.0 GV.SC-07 (The risks posed by a supplier, their products and services, and other third parties are understood, recorded, prioritized, assessed, responded to, and monitored over the cour…
- `xwalk:row33`: Official crosswalk row 33: CSF 2.0 GV.SC-09 (Supply chain security practices are integrated into cybersecurity and enterprise risk management programs, and their performance is monitored throughout the technology produc…
- `xwalk:row34`: Official crosswalk row 34: CSF 2.0 GV.SC-10 (Cybersecurity supply chain risk management plans include provisions for activities that occur after the conclusion of a partnership or service agreement) -> CSF 1.1 ID.SC-1 (…
- `xwalk:row77`: Official crosswalk row 77: CSF 2.0 ID.RA-10 (Critical suppliers are assessed prior to acquisition) -> CSF 1.1 ID.SC-2 (Suppliers and third party partners of information systems, components, and services are identified, …

</details>

### Expected (existing gold dataset; never shown to the generator)

- Expected crosswalk rows: [22]
- Expected mappings: row 22: GV.SC → ID.SC
- Expected facts: Official row 22: GV.SC -> ID.SC [xwalk:row22]

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | PASS |  |
| mapping_cites_matching_row | PASS |  |
| versions_correct | PASS |  |
| expected_rows_covered | FAIL | official rows not cited: [22] |
| expected_controls_referenced | N/A |  |
| conflict_preserved | N/A |  |
| new_control_no_reference | N/A |  |
| no_forbidden_mappings | N/A |  |
| no_unsupported_removal | PASS |  |
| no_uncited_claims | PASS |  |

**Expected rows missing from the answer:** `xwalk:row22`
- **RETRIEVAL FAILURE:** `xwalk:row22` was never in the evidence supplied to the generator, so the model could not cite it.

### Needs human verification (semantic; NOT assessed by any check)

- `S1` In CSF 1.1, supply chain risk management is primarily addressed under the Identify function with two subcategories: ID.SC-1 (processes identified and establish… — no citation attached to this sentence (check it against the answer-level citations)
- `S2` In CSF 2.0, this focus is significantly expanded and restructured. — no citation attached to this sentence (check it against the answer-level citations)
- `S3` A new category, Cybersecurity Supply Chain Risk Management (GV.SC), is introduced under the Govern function, containing multiple subcategories (GV.SC-01 throug… — no citation attached to this sentence (check it against the answer-level citations)
- `S4` Additionally, CSF 2.0 includes GV.RM-05 for communication lines regarding supplier risks and ID.RA-10 for assessing critical suppliers prior to acquisition. — no citation attached to this sentence (check it against the answer-level citations)
- `S5` The official crosswalk maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories, indicating a shift from a limited identification focus to a … — no citation attached to this sentence (check it against the answer-level citations)
- `K1` CSF 2.0 introduces a dedicated 'Cybersecurity Supply Chain Risk Management' category (GV.SC) under the Govern function, whereas CSF 1.1 only had subcategories … — cited: `chunk:csf2.0:text:65a38d02bf94`, `chunk:csf1.1:subcategory:ID.SC-1`, `chunk:csf1.1:subcategory:ID.SC-2`
- `K2` CSF 2.0 expands the scope to include specific governance activities such as establishing a program/strategy (GV.SC-01), integrating with enterprise risk manage… — cited: `chunk:csf2.0:subcategory:GV.SC-01`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:subcategory:GV.SC-06`, `chunk:csf2.0:subcategory:GV.SC-09`, `chunk:csf2.0:subcategory:GV.SC-10`
- `K3` CSF 2.0 adds specific requirements for assessing critical suppliers prior to acquisition (ID.RA-10) and establishing lines of communication for supplier risks … — cited: `chunk:csf2.0:subcategory:ID.RA-10`, `chunk:csf2.0:subcategory:GV.RM-05`
- `M1` Mapping claim: GV.RM-05 -> ID.SC-1. Official crosswalk maps GV.RM-05 to ID.SC-1. — cited: `xwalk:row19`
- `M2` Mapping claim: GV.SC-01 -> ID.SC-1. Official crosswalk maps GV.SC-01 to ID.SC-1. — cited: `xwalk:row23`
- `M3` Mapping claim: GV.SC-03 -> ID.SC-2. Official crosswalk maps GV.SC-03 to ID.SC-2. — cited: `xwalk:row25`
- `M4` Mapping claim: GV.SC-04 -> ID.SC-2. Official crosswalk maps GV.SC-04 to ID.SC-2. — cited: `xwalk:row27`
- `M5` Mapping claim: GV.SC-06 -> ID.SC-1. Official crosswalk maps GV.SC-06 to ID.SC-1. — cited: `xwalk:row29`
- `M6` Mapping claim: GV.SC-07 -> ID.SC-2. Official crosswalk maps GV.SC-07 to ID.SC-2. — cited: `xwalk:row30`
- `M7` Mapping claim: GV.SC-09 -> ID.SC-1. Official crosswalk maps GV.SC-09 to ID.SC-1. — cited: `xwalk:row33`
- `M8` Mapping claim: GV.SC-10 -> ID.SC-1. Official crosswalk maps GV.SC-10 to ID.SC-1. — cited: `xwalk:row34`
- `M9` Mapping claim: ID.RA-10 -> ID.SC-2. Official crosswalk maps ID.RA-10 to ID.SC-2. — cited: `xwalk:row77`
- Mapping GV.RM-05 → ID.SC-1 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-01 → ID.SC-1 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-03 → ID.SC-2 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-04 → ID.SC-2 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-06 → ID.SC-1 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-07 → ID.SC-2 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-09 → ID.SC-1 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping GV.SC-10 → ID.SC-1 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.
- Mapping ID.RA-10 → ID.SC-2 is not among the gold rows for this question; the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 3945 prompt + 1857 output = 5802
- Latency: 79.629 s — Generation latency includes a 75 s pacing wait before the request; the API call itself took a few seconds.
- Attempts: 1; rejections: none; warnings: ['6 lower-ranked passage(s) were left out of the prompt for space.']
- Source artifact: `eval/live_runs/2026-10-22_six_question_qwen_gptoss_partial_stopped_at_B01.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)

---

## C01 — official_mapping

**Question:** How does GV.OC-01 map to CSF 1.1?

### Actual output

According to the official crosswalk, the CSF 2.0 subcategory GV.OC-01 maps to two CSF 1.1 subcategories: ID.BE-2 and ID.BE-3.

**Key changes**

- GV.OC-01 (CSF 2.0) is mapped to ID.BE-2 (CSF 1.1). `xwalk:row4`
- GV.OC-01 (CSF 2.0) is mapped to ID.BE-3 (CSF 1.1). `xwalk:row5`

**Mappings**

- GV.OC-01 → ID.BE-2 — Official crosswalk mapping from CSF 2.0 to CSF 1.1. `xwalk:row4`
- GV.OC-01 → ID.BE-3 — Official crosswalk mapping from CSF 2.0 to CSF 1.1. `xwalk:row5`

**Answer-level citations:** `xwalk:row4`, `xwalk:row5`, `chunk:csf2.0:subcategory:GV.OC-01`, `chunk:csf1.1:subcategory:ID.BE-2`, `chunk:csf1.1:subcategory:ID.BE-3`

### Evidence supplied to the generator

10 items: `chunk:csf1.1:subcategory:ID.BE-2`, `chunk:csf1.1:subcategory:ID.BE-3`, `chunk:csf1.1:text:409dec4508b8`, `chunk:csf1.1:text:4dd835ba7743`, `chunk:csf1.1:text:9a8b2283038f`, `chunk:csf2.0:subcategory:GV.OC-01`, `chunk:csf2.0:text:65a38d02bf94`, `chunk:csf2.0:text:a199d63dc39b`, `xwalk:row4`, `xwalk:row5`

<details><summary>Cited evidence text</summary>

- `chunk:csf1.1:subcategory:ID.BE-2`: ID.BE-2: The organization’s place in critical infrastructure and its industry sector is identified and communicated
- `chunk:csf1.1:subcategory:ID.BE-3`: ID.BE-3: Priorities for organizational mission, objectives, and activities are established and communicated
- `chunk:csf2.0:subcategory:GV.OC-01`: GV.OC-01: The organizational mission is understood and informs cybersecurity risk management
- `xwalk:row4`: Official crosswalk row 4: CSF 2.0 GV.OC-01 (The organizational mission is understood and informs cybersecurity risk management) -> CSF 1.1 ID.BE-2 (The organization’s place in critical infrastructure and its industry se…
- `xwalk:row5`: Official crosswalk row 5: CSF 2.0 GV.OC-01 (The organizational mission is understood and informs cybersecurity risk management) -> CSF 1.1 ID.BE-3 (Priorities for organizational mission, objectives, and activities are e…

</details>

### Expected (existing gold dataset; never shown to the generator)

- Expected crosswalk rows: [4, 5]
- Expected mappings: row 4: GV.OC-01 → ID.BE-2; row 5: GV.OC-01 → ID.BE-3
- Expected facts: Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]; Official row 5: GV.OC-01 -> ID.BE-3 [xwalk:row5]

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | PASS |  |
| mapping_cites_matching_row | PASS |  |
| versions_correct | PASS |  |
| expected_rows_covered | PASS |  |
| expected_controls_referenced | PASS |  |
| conflict_preserved | N/A |  |
| new_control_no_reference | N/A |  |
| no_forbidden_mappings | N/A |  |
| no_unsupported_removal | PASS |  |
| no_uncited_claims | PASS |  |

**Expected rows missing from the answer:** none

### Needs human verification (semantic; NOT assessed by any check)

- `S1` According to the official crosswalk, the CSF 2.0 subcategory GV.OC-01 maps to two CSF 1.1 subcategories: ID.BE-2 and ID.BE-3. — no citation attached to this sentence (check it against the answer-level citations)
- `K1` GV.OC-01 (CSF 2.0) is mapped to ID.BE-2 (CSF 1.1). — cited: `xwalk:row4`
- `K2` GV.OC-01 (CSF 2.0) is mapped to ID.BE-3 (CSF 1.1). — cited: `xwalk:row5`
- `M1` Mapping claim: GV.OC-01 -> ID.BE-2. Official crosswalk mapping from CSF 2.0 to CSF 1.1. — cited: `xwalk:row4`
- `M2` Mapping claim: GV.OC-01 -> ID.BE-3. Official crosswalk mapping from CSF 2.0 to CSF 1.1. — cited: `xwalk:row5`

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 2850 prompt + 476 output = 3326
- Latency: 6.764 s
- Attempts: 1; rejections: none; warnings: none
- Source artifact: `eval/live_runs/2026-10-22_generation_C01_F01_E01_H02.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)

---

## F01 — conflict

**Question:** How does GV.SC-03 map to CSF 1.1?

### Actual output

According to the official crosswalk, CSF 2.0 subcategory GV.SC-03 maps to CSF 1.1 subcategory ID.SC-2. However, the official workbook also contains a separate entry indicating that GV.SC-03 is 'conceptually new in 2.0' with no corresponding CSF 1.1 reference. Both entries are present in the official records.

**Key changes**

- CSF 2.0 GV.SC-03 is mapped to CSF 1.1 ID.SC-2 in the official crosswalk. `xwalk:row25`
- CSF 2.0 GV.SC-03 is also listed as 'conceptually new in 2.0' with no CSF 1.1 reference in the official crosswalk. `xwalk:row26`

**Mappings**

- GV.SC-03 → ID.SC-2 — Official crosswalk row 25 maps GV.SC-03 to ID.SC-2. `xwalk:row25`
- GV.SC-03 → (no CSF 1.1 reference) — Official crosswalk row 26 lists GV.SC-03 as 'new_in_2_0' with the comment 'Conceptually new in 2.0' and no reference ID. `xwalk:row26`

**Uncertainties stated by the answer**

- The official crosswalk contains conflicting entries for GV.SC-03: one mapping it to ID.SC-2 and another marking it as conceptually new in 2.0 with no 1.1 reference. Both are reported as per pipeline findings.

**Answer-level citations:** `xwalk:row25`, `xwalk:row26`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf1.1:subcategory:ID.SC-2`

### Evidence supplied to the generator

10 items: `chunk:csf1.1:subcategory:ID.SC-2`, `chunk:csf1.1:text:409dec4508b8`, `chunk:csf1.1:text:4dd835ba7743`, `chunk:csf1.1:text:9a8b2283038f`, `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf2.0:text:2400d2aa8dcf`, `chunk:csf2.0:text:65a38d02bf94`, `chunk:csf2.0:text:a199d63dc39b`, `xwalk:row25`, `xwalk:row26`

<details><summary>Cited evidence text</summary>

- `chunk:csf1.1:subcategory:ID.SC-2`: ID.SC-2: Suppliers and third party partners of information systems, components, and services are identified, prioritized, and assessed using a cyber supply chain risk assessment process
- `chunk:csf2.0:subcategory:GV.SC-03`: GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes
- `xwalk:row25`: Official crosswalk row 25: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 ID.SC-2 (Su…
- `xwalk:row26`: Official crosswalk row 26: CSF 2.0 GV.SC-03 (Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes) -> CSF 1.1 NO REFERENC…

</details>

### Expected (existing gold dataset; never shown to the generator)

- Expected crosswalk rows: [25, 26]
- Expected mappings: row 25: GV.SC-03 → ID.SC-2; row 26: GV.SC-03 → (none)
- Conflict rows (both must be preserved): [25, 26]
- Expected facts: Official row 25: GV.SC-03 -> ID.SC-2 [xwalk:row25]; Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | PASS |  |
| mapping_cites_matching_row | PASS |  |
| versions_correct | PASS |  |
| expected_rows_covered | PASS |  |
| expected_controls_referenced | PASS |  |
| conflict_preserved | PASS |  |
| new_control_no_reference | N/A |  |
| no_forbidden_mappings | N/A |  |
| no_unsupported_removal | PASS |  |
| no_uncited_claims | PASS |  |

**Expected rows missing from the answer:** none

### Needs human verification (semantic; NOT assessed by any check)

- `S1` According to the official crosswalk, CSF 2.0 subcategory GV.SC-03 maps to CSF 1.1 subcategory ID.SC-2. — no citation attached to this sentence (check it against the answer-level citations)
- `S2` However, the official workbook also contains a separate entry indicating that GV.SC-03 is 'conceptually new in 2.0' with no corresponding CSF 1.1 reference. — no citation attached to this sentence (check it against the answer-level citations)
- `S3` Both entries are present in the official records. — no citation attached to this sentence (check it against the answer-level citations)
- `K1` CSF 2.0 GV.SC-03 is mapped to CSF 1.1 ID.SC-2 in the official crosswalk. — cited: `xwalk:row25`
- `K2` CSF 2.0 GV.SC-03 is also listed as 'conceptually new in 2.0' with no CSF 1.1 reference in the official crosswalk. — cited: `xwalk:row26`
- `M1` Mapping claim: GV.SC-03 -> ID.SC-2. Official crosswalk row 25 maps GV.SC-03 to ID.SC-2. — cited: `xwalk:row25`
- `M2` Mapping claim: GV.SC-03 -> no CSF 1.1 reference. Official crosswalk row 26 lists GV.SC-03 as 'new_in_2_0' with the comment 'Conceptually new in 2.0' and no ref… — cited: `xwalk:row26`

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 3141 prompt + 576 output = 3717
- Latency: 76.863 s
- Attempts: 1; rejections: none; warnings: none
- Source artifact: `eval/live_runs/2026-10-22_generation_C01_F01_E01_H02.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)

---

## E01 — conceptually_new

**Question:** How does GV.OV-01 map to CSF 1.1?

### Actual output

GV.OV-01 does not map to any CSF 1.1 element. The official crosswalk identifies GV.OV-01 as 'new_in_2_0' with the comment 'Conceptually new in 2.0', indicating there is no corresponding CSF 1.1 reference element.

**Key changes**

- GV.OV-01 is a new subcategory in CSF 2.0 with no direct equivalent in CSF 1.1. `xwalk:row46`

**Mappings**

- GV.OV-01 → (no CSF 1.1 reference) — Official crosswalk marks this element as conceptually new in CSF 2.0 with no CSF 1.1 reference. `xwalk:row46`

**Answer-level citations:** `xwalk:row46`, `chunk:csf2.0:subcategory:GV.OV-01`

### Evidence supplied to the generator

8 items: `chunk:csf1.1:text:409dec4508b8`, `chunk:csf1.1:text:4dd835ba7743`, `chunk:csf1.1:text:9a8b2283038f`, `chunk:csf2.0:subcategory:GV.OV-01`, `chunk:csf2.0:text:2400d2aa8dcf`, `chunk:csf2.0:text:65a38d02bf94`, `chunk:csf2.0:text:a199d63dc39b`, `xwalk:row46`

<details><summary>Cited evidence text</summary>

- `chunk:csf2.0:subcategory:GV.OV-01`: GV.OV-01: Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction
- `xwalk:row46`: Official crosswalk row 46: CSF 2.0 GV.OV-01 (Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction) -> CSF 1.1 NO REFERENCE (); mapping_type=new_in_2_0; comments=Concep…

</details>

### Expected (existing gold dataset; never shown to the generator)

- Expected crosswalk rows: [46]
- Expected mappings: row 46: GV.OV-01 → (none)
- Conceptually new in 2.0 (no CSF 1.1 reference): ['GV.OV-01']
- Expected facts: Official row 46: GV.OV-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row46]

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | PASS |  |
| mapping_cites_matching_row | PASS |  |
| versions_correct | PASS |  |
| expected_rows_covered | PASS |  |
| expected_controls_referenced | PASS |  |
| conflict_preserved | N/A |  |
| new_control_no_reference | PASS |  |
| no_forbidden_mappings | N/A |  |
| no_unsupported_removal | PASS |  |
| no_uncited_claims | PASS |  |

**Expected rows missing from the answer:** none

### Needs human verification (semantic; NOT assessed by any check)

- `S1` GV.OV-01 does not map to any CSF 1.1 element. — no citation attached to this sentence (check it against the answer-level citations)
- `S2` The official crosswalk identifies GV.OV-01 as 'new_in_2_0' with the comment 'Conceptually new in 2.0', indicating there is no corresponding CSF 1.1 reference e… — no citation attached to this sentence (check it against the answer-level citations)
- `K1` GV.OV-01 is a new subcategory in CSF 2.0 with no direct equivalent in CSF 1.1. — cited: `xwalk:row46`
- `M1` Mapping claim: GV.OV-01 -> no CSF 1.1 reference. Official crosswalk marks this element as conceptually new in CSF 2.0 with no CSF 1.1 reference. — cited: `xwalk:row46`

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 2868 prompt + 314 output = 3182
- Latency: 76.343 s
- Attempts: 1; rejections: none; warnings: none
- Source artifact: `eval/live_runs/2026-10-22_generation_C01_F01_E01_H02.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)

---

## H02 — abstention

**Question:** Which CSF control requires quantum-safe cryptography?

### Actual output

**ABSTAINED.** Reason given: The supplied evidence does not contain any reference to quantum-safe cryptography or any control requiring it.

### Evidence supplied to the generator

10 items: `chunk:csf1.1:category:PR.AC`, `chunk:csf1.1:subcategory:PR.AC-2`, `chunk:csf1.1:subcategory:PR.AC-6`, `chunk:csf1.1:subcategory:PR.AC-7`, `chunk:csf1.1:text:5f324aa8fadc`, `chunk:csf2.0:text:792797730b74`, `chunk:csf2.0:text:7bd323c1a541`, `chunk:csf2.0:text:b38e21279ced`, `chunk:csf2.0:text:d79f84dd4aeb`, `chunk:csf2.0:text:e4b22429b8ae`

### Expected (existing gold dataset; never shown to the generator)

- Must abstain (basis: topic_absent). The corpus has no cryptography content at all; any retrieved passage is off-topic.
- Expected crosswalk rows: none
- Expected mappings: none
- Expected facts: none

### Deterministic validation (machine-checked)

| Check | Result | Detail |
|---|---|---|
| schema_valid | PASS |  |
| citation_ids_valid | PASS |  |
| citations_in_bundle | PASS |  |
| abstention_correct | PASS |  |
| mapping_pairs_official | N/A | answer abstained |
| mapping_cites_matching_row | N/A | answer abstained |
| versions_correct | N/A | answer abstained |
| expected_rows_covered | N/A | answer abstained |
| expected_controls_referenced | N/A | answer abstained |
| conflict_preserved | N/A | answer abstained |
| new_control_no_reference | N/A | answer abstained |
| no_forbidden_mappings | N/A | answer abstained |
| no_unsupported_removal | N/A | answer abstained |
| no_uncited_claims | N/A | answer abstained |

### Needs human verification (semantic; NOT assessed by any check)

- Confirm the abstention reason is accurate and does not invent content.

### Generation details

- Generator: `groq` / `qwen/qwen3.8-27b` (reported: qwen/qwen3.8-27b)
- Tokens: 2958 prompt + 242 output = 3200
- Latency: 76.21 s
- Attempts: 1; rejections: none; warnings: none
- Source artifact: `eval/live_runs/2026-10-22_generation_C01_F01_E01_H02.json`

**Human review status:** not performed (no human sign-off) (reviewer: —)
