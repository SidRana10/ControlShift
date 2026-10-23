# B01 — original vs first correction vs final (three versions)

**Question (unchanged, exact original):** What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

> **Read this first.** A single question, repaired after seeing its failures. These are **post-hoc repair criteria, not an unbiased benchmark**, and no accuracy,
> faithfulness or judge scores are given. The original gold dataset (it expects only crosswalk row 22) is unchanged and drives the deterministic check.
> Three kinds of statement are kept apart: **[M] machine-checked** results, **[S] source-supported preliminary observations** (my reading of the answer against the stored
> official records — not a verdict), and **[H] items awaiting human review**.

- **A. Original:** `eval/live_runs/2026-10-22_six_question_qwen_gptoss_partial_stopped_at_B01.json` (unchanged)
- **B. First corrected** (category expansion, rows only): `eval/live_runs/2026-10-22_B01_retest_after_category_expansion.json` (unchanged)
- **C. Final** (canonical definitions prioritised, strict budget): `eval/live_runs/2026-10-22_B01_final_retest_budget_priority.json`

## 0. Recorded status (read first)
> Data note: the original workbook has no `mapping_type` column; "mapped" / "new_in_2_0" are ControlShift-derived labels (reference present / no reference and a "new" comment). Source facts below were also read from the original PDFs/workbook by an AI assistant; no human has signed off.
- **Baseline:** the six-question evaluation uses the ORIGINAL B01 (A). Repairs B and C are separate post-hoc results.
- **Original retrieval omission:** row 22 and ID.SC-3/4/5 never reached the generator.
- **Incorrect two-subcategory claim:** A says CSF 1.1 has two supply-chain subcategories; it has five.
- **Recovered:** official crosswalk row 22 (from B onward); improved category-aware evidence selection (B, then definitions-first in C); strict 12,000-character context budget (C: 11,963).
- **Still open in C:** no explanation of what ID.SC-3/4/5 cover; possibly overstated novelty ("new concepts" for GV.SC items that the crosswalk maps to ID.SC-1/ID.SC-2); some mapping rows omitted for space (disclosed by the answer).
- **No version is described as fully correct or complete.** Human confirmation is PENDING; machine results are [M], readings of the answers are [AI], and nothing is [H] yet.

## 1. What was wrong and what changed
| Step | Problem found | Change |
|---|---|---|
| A → B | Category chunk (ID.SC, rank 6) and ID.SC-3/4/5 were never retrieved; row 22 and the ID.SC-3/4/5 rows never reached the model; answer said CSF 1.1 had "two subcategories". | Category-aware expansion for broad comparisons: category record + official rows of the category and its subcategories (both versions). |
| B → C | B carried mappings but not the canonical *definitions* of ID.SC-3/4/5 and GV.SC-xx (they were dropped as "counterpart" records), so the answer could not say what they cover; the serialized evidence was 12,138 chars against a 12,000 budget (merge markers and separators were not counted), and the budget was enforced in two places. | Expansion now keeps every subcategory record in the (complete) structured bundle; the context builder alone enforces the budget on the FINAL text (blocks, attributes, separators) with a deterministic priority: category definitions → subcategory definitions of the compared categories → category-level mappings → conflicting rows → other mappings inside the compared categories → mappings reaching outside → other control records → passages. Official records are never cut; what does not fit is omitted and reported in `missing_evidence`. |

## 2. Machine-checked results [M]
| | A. Original | B. First corrected | C. Final |
|---|---|---|---|
| Applicable deterministic checks failed | expected_rows_covered: official rows not cited: [22] | none | none |
| Row 22 cited | no | yes | yes |
| Official mappings in the answer | 9 (all official) | 13 (all official) | 10 (all official) |
| GV.SC-03 conflict rows 25 + 26 cited | no | yes | yes |
| Evidence items supplied to the generator | 24 | 23 | 27 |
| Serialized evidence (chars; budget 12,000) | 11,940 | 12,138 (over) | **11963** (configured 12000) |
| Full prompt (chars) | — | — | 13783 |
| Qwen tokens (prompt + output = total) | 3945 + 1857 = 5802 | 4223 + 1984 = 6207 | 4455 + 1979 = 6434 |
| API latency (single request) | ≈4.6 s (79.6 s recorded minus a 75 s pacing wait) | 8.7 s | 7.671 s |
| Requests | 1 | 1 | 1 (0 judge, 0 Gemini, 0 Mistral) |
| Omitted official records reported in `missing_evidence` | n/a | n/a | yes — 2 warnings: 11 official record(s) were left out of the prompt for space.; 10 lower-ranked passage(s) were left out of the prompt for space. |

## 3. Source-verified criteria (post-hoc)
Source facts (stored official records): CSF 1.1 ID.SC has five subcategories — ID.SC-1 (processes), ID.SC-2 (suppliers identified/prioritized/assessed), ID.SC-3
(contracts implement measures), ID.SC-4 (suppliers routinely assessed against contractual obligations), ID.SC-5 (response and recovery planning/testing with
suppliers); CSF 2.0 GV.SC has ten; row 22 maps the categories GV.SC → ID.SC; rows 25 and 26 are the GV.SC-03 conflict.

| # | Criterion | A | B | C — preliminary observation [S] (human confirmation [H] PENDING) |
|---|---|---|---|---|
| 1 | Describes CSF 1.1's five ID.SC subcategories | No (says two) | Partly (false claim gone; five appear only via mappings) | **Yes, as an enumeration**: "ID.SC-1 through ID.SC-5" in the category it names; no per-subcategory description |
| 2 | Explains the roles of ID.SC-3, -4, -5 | No | No | **No.** Their definitions were in the evidence and cited at answer level, but the answer never says what they cover; only ID.SC-3 appears (in the GV.SC-05 mapping). The main remaining gap. |
| 3 | Move from Identify to Govern | Partly | Yes | **Yes** (cites both category records and row 22) |
| 4 | Row 22 preserved | No | Yes | **Yes** [M] |
| 5 | Distinguishes existing 1.1 concepts from 2.0 evolution | Weak | Partly | **Weak/partly.** It calls GV.SC-06, -03 and -10 "new concepts"/"introduces", yet the same answer maps them to ID.SC-1/ID.SC-2 (rows 29, 25, 34), i.e. the crosswalk treats them as evolutions of 1.1 outcomes. A reviewer should check this framing. |
| 6 | Preserves official mapping conflicts | n/a | Yes | **Yes** [M]: rows 25 and 26 both cited and the conflict stated |
| 7 | No fabricated or unsupported claims | "two subcategories" false | no known false fact | **No known false fact**; every mapping is an official row [M]. Questionable: "new concepts … (GV.SC-06)", "a more granular set of controls" (interpretation). [H] |
| 8 | Relevant evidence and citations | partly | yes | **Yes**: 27 citations, all in the supplied evidence [M]; includes both category records and the canonical definitions of all five ID.SC subcategories |
| 9 | Acknowledges genuinely missing evidence | partly | yes | **Yes**: says some official records were omitted for the context budget and names GV.SC-02, GV.SC-08, ID.SC-4, ID.SC-5 as lacking mapping rows |
| 10 | Passes applicable deterministic checks | **No** (row 22) | Yes | **Yes** [M] |

**Other differences to weigh [H]:** C no longer includes GV.SC-02→ID.AM-6 (row 24), GV.SC-07→ID.SC-4 (row 31), GV.SC-08→ID.SC-5 (row 32) and the rows that map other categories into ID.SC
(6, 19, 77, 78, 84): they are in the structured evidence but did not fit the 12,000-character context, and the answer says so. B had rows 24 and 31–32 but not the canonical definitions; C has the
definitions but not those rows. The trade-off follows the stated priority (definitions before subcategory mappings); the default budget was not raised.

## 4. Verdict
- **Resolved [M]:** row-22 retrieval omission; false "two subcategories" claim; budget overshoot (11,963 ≤ 12,000 on the serialized evidence, enforced in one place); omissions are explicit.
- **Improved but not complete [S]:** the answer now enumerates ID.SC-1…5 and moves Identify → Govern correctly.
- **Remaining limitation (documented, not optimised further):** the generator does not turn the supplied ID.SC-3/4/5 definitions into an explanation of their roles, and its "new concept" framing of
  mapped GV.SC items may overstate novelty. Both need human review; this was the last planned backend iteration.
- **Human verification: PENDING** (see `eval/human_verification_checklist.md`).

## 5. Answers
### A. Original
In CSF 1.1, supply chain risk management is primarily addressed under the Identify function with two subcategories: ID.SC-1 (processes identified and established) and ID.SC-2 (suppliers identified, prioritized, and assessed). In CSF 2.0, this focus is significantly expanded and restructured. A new category, Cybersecurity Supply Chain Risk Management (GV.SC), is introduced under the Govern function, containing multiple subcategories (GV.SC-01 through GV.SC-10) that cover program establishment, integration with enterprise risk management, supplier prioritization, due diligence, lifecycle monitoring, and post-contract activities. Additionally, CSF 2.0 includes GV.RM-05 for communication lines regarding supplier risks and ID.RA-10 for assessing critical suppliers prior to acquisition. The official crosswalk maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories, indicating a shift from a limited identification focus to a comprehensive governance and lifecycle management approach.

**Key changes**
- CSF 2.0 introduces a dedicated 'Cybersecurity Supply Chain Risk Management' category (GV.SC) under the Govern function, whereas CSF 1.1 only had subcategories under the Identify function (ID.SC). `chunk:csf2.0:text:65a38d02bf94, chunk:csf1.1:subcategory:ID.SC-1, chunk:csf1.1:subcategory:ID.SC-2`
- CSF 2.0 expands the scope to include specific governance activities such as establishing a program/strategy (GV.SC-01), integrating with enterprise risk management (GV.SC-03, GV.SC-09), performing due diligence before relationships (GV.SC-06), and planning for post-contract activities (GV.SC-10), which are not explicitly detailed as separate subcategories in CSF 1.1. `chunk:csf2.0:subcategory:GV.SC-01, chunk:csf2.0:subcategory:GV.SC-03, chunk:csf2.0:subcategory:GV.SC-06, chunk:csf2.0:subcategory:GV.SC-09, chunk:csf2.0:subcategory:GV.SC-10`
- CSF 2.0 adds specific requirements for assessing critical suppliers prior to acquisition (ID.RA-10) and establishing lines of communication for supplier risks (GV.RM-05). `chunk:csf2.0:subcategory:ID.RA-10, chunk:csf2.0:subcategory:GV.RM-05`

**Mappings**
- GV.RM-05 → ID.SC-1 `xwalk:row19`
- GV.SC-01 → ID.SC-1 `xwalk:row23`
- GV.SC-03 → ID.SC-2 `xwalk:row25`
- GV.SC-04 → ID.SC-2 `xwalk:row27`
- GV.SC-06 → ID.SC-1 `xwalk:row29`
- GV.SC-07 → ID.SC-2 `xwalk:row30`
- GV.SC-09 → ID.SC-1 `xwalk:row33`
- GV.SC-10 → ID.SC-1 `xwalk:row34`
- ID.RA-10 → ID.SC-2 `xwalk:row77`

**Uncertainties stated by the answer**
- The evidence does not provide a complete list of all CSF 2.0 subcategories under GV.SC, only specific ones (01, 03, 04, 06, 07, 09, 10).
- The evidence does not explicitly state if any CSF 1.1 supply chain controls were removed, only that they were mapped to new CSF 2.0 controls.

### B. First corrected
The primary structural difference is that CSF 1.1 places Supply Chain Risk Management (ID.SC) within the Identify function, whereas CSF 2.0 moves it to the Govern function as Cybersecurity Supply Chain Risk Management (GV.SC). In CSF 1.1, the category description emphasizes establishing priorities, constraints, and risk tolerances to support risk decisions. In CSF 2.0, the category description emphasizes that processes are identified, established, managed, monitored, and improved by organizational stakeholders. The CSF 2.0 subcategories are more granular, covering specific aspects like program establishment (GV.SC-01), integration into enterprise risk management (GV.SC-03), supplier prioritization (GV.SC-04), contract requirements (GV.SC-05), due diligence (GV.SC-06), ongoing risk monitoring (GV.SC-07), incident planning inclusion (GV.SC-08), life-cycle monitoring (GV.SC-09), and post-agreement activities (GV.SC-10).

**Key changes**
- CSF 1.1 locates Supply Chain Risk Management in the Identify function (ID.SC), while CSF 2.0 locates it in the Govern function (GV.SC). `chunk:csf1.1:category:ID.SC, chunk:csf2.0:category:GV.SC`
- The CSF 1.1 category description focuses on establishing priorities, constraints, risk tolerances, and assumptions to support risk decisions. `chunk:csf1.1:category:ID.SC`
- The CSF 2.0 category description focuses on processes being identified, established, managed, monitored, and improved by organizational stakeholders. `chunk:csf2.0:category:GV.SC`
- CSF 2.0 introduces specific subcategories for supplier prioritization (GV.SC-04), contract integration (GV.SC-05), and due diligence (GV.SC-06) that are mapped to broader CSF 1.1 subcategories. `xwalk:row27, xwalk:row28, xwalk:row29`
- CSF 2.0 includes subcategories for post-agreement activities (GV.SC-10) and life-cycle monitoring (GV.SC-09) which are mapped to the general CSF 1.1 ID.SC-1 subcategory. `xwalk:row34, xwalk:row33`

**Mappings**
- GV.SC → ID.SC `xwalk:row22`
- GV.SC-01 → ID.SC-1 `xwalk:row23`
- GV.SC-02 → ID.AM-6 `xwalk:row24`
- GV.SC-03 → ID.SC-2 `xwalk:row25`
- GV.SC-03 → (no CSF 1.1 reference) `xwalk:row26`
- GV.SC-04 → ID.SC-2 `xwalk:row27`
- GV.SC-05 → ID.SC-3 `xwalk:row28`
- GV.SC-06 → ID.SC-1 `xwalk:row29`
- GV.SC-07 → ID.SC-2 `xwalk:row30`
- GV.SC-07 → ID.SC-4 `xwalk:row31`
- GV.SC-08 → ID.SC-5 `xwalk:row32`
- GV.SC-09 → ID.SC-1 `xwalk:row33`
- GV.SC-10 → ID.SC-1 `xwalk:row34`

**Uncertainties stated by the answer**
- The official crosswalk lists GV.SC-03 as both mapped to ID.SC-2 and as 'conceptually new in 2.0'; both entries are reported as per pipeline findings.
- Specific text for CSF 2.0 subcategories GV.SC-01, GV.SC-03, GV.SC-04, GV.SC-06, GV.SC-07, GV.SC-09, and GV.SC-10 was omitted from the evidence budget, so their full definitions are not quoted here, though their descriptions are provided in the crosswalk rows.
- CSF 1.1 subcategories ID.SC-3, ID.SC-4, and ID.SC-5 are referenced in the crosswalk but their full control records were not provided in the evidence blocks, only their descriptions within the crosswalk rows.

### C. Final
In CSF 1.1, supply chain risk management is located in the Identify function under the category ID.SC, with specific subcategories ID.SC-1 through ID.SC-5. In CSF 2.0, this area is moved to the Govern function under the category GV.SC, with subcategories GV.SC-01 through GV.SC-10. The 2.0 version introduces a more granular set of controls, including new concepts such as planning and due diligence before entering relationships (GV.SC-06), integration into enterprise risk management (GV.SC-03), and provisions for post-contract activities (GV.SC-10). The official crosswalk maps the 2.0 category GV.SC to the 1.1 category ID.SC, and maps specific 2.0 subcategories to their 1.1 counterparts, though some 2.0 controls are marked as conceptually new.

**Key changes**
- The category for supply chain risk management moved from Identify (ID.SC) in CSF 1.1 to Govern (GV.SC) in CSF 2.0. `chunk:csf1.1:category:ID.SC, chunk:csf2.0:category:GV.SC, xwalk:row22`
- CSF 2.0 introduces GV.SC-06, which requires planning and due diligence to reduce risks before entering into formal supplier relationships, a specific requirement not explicitly present as a standalone subcategory in the provided CSF 1.1 evidence. `chunk:csf2.0:subcategory:GV.SC-06, xwalk:row29`
- CSF 2.0 introduces GV.SC-10, which requires supply chain risk management plans to include provisions for activities after the conclusion of a partnership or service agreement. `chunk:csf2.0:subcategory:GV.SC-10, xwalk:row34`
- CSF 2.0 GV.SC-03 is mapped to CSF 1.1 ID.SC-2 but is also listed as 'new_in_2_0' with the comment 'Conceptually new in 2.0', indicating a conflict in the official workbook regarding its novelty. `xwalk:row25, xwalk:row26`
- CSF 2.0 GV.SC-09 emphasizes monitoring supply chain security practices throughout the technology product and service life cycle, mapped to CSF 1.1 ID.SC-1. `chunk:csf2.0:subcategory:GV.SC-09, xwalk:row33`

**Mappings**
- GV.SC → ID.SC `xwalk:row22`
- GV.SC-01 → ID.SC-1 `xwalk:row23`
- GV.SC-03 → ID.SC-2 `xwalk:row25`
- GV.SC-03 → (no CSF 1.1 reference) `xwalk:row26`
- GV.SC-04 → ID.SC-2 `xwalk:row27`
- GV.SC-05 → ID.SC-3 `xwalk:row28`
- GV.SC-06 → ID.SC-1 `xwalk:row29`
- GV.SC-07 → ID.SC-2 `xwalk:row30`
- GV.SC-09 → ID.SC-1 `xwalk:row33`
- GV.SC-10 → ID.SC-1 `xwalk:row34`

**Uncertainties stated by the answer**
- The evidence is an excerpt; some records (e.g., GV.SC-02, GV.SC-08, ID.SC-4, ID.SC-5) are present in the evidence blocks but their specific crosswalk mappings are not provided in the supplied xwalk rows, so their 1.1 counterparts are not listed in the mappings array.
- The official workbook contains conflicting entries for GV.SC-03, listing it as both mapped to ID.SC-2 and as new_in_2_0.
- Missing evidence indicates that some official records were omitted for context budget, so the coverage of the comparison may be incomplete.
