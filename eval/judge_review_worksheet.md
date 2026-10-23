# Judge calibration worksheet

Edit `eval/judge_calibration.json` (not this file): set `status` to `reviewed`, add your name, give each of the five dimensions an integer 1-5 using the rubric in `eval/judge_report.md`, and record any disagreement with the LLM judge in `disagreement_notes`. **All human fields are currently pending unless shown otherwise.**

## A01 - What does GV.SC-03 require?

- Category: `exact_control`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- GV.SC-03 integrates supply chain risk management into broader risk processes. [chunk:csf2.0:subcategory:GV.SC-03] - "Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes"

**Gemini answer**

In NIST CSF 2.0, GV.SC-03 requires that cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes.

- citations: ['chunk:csf2.0:subcategory:GV.SC-03']
- mappings: []

**Source evidence cited**

- `chunk:csf2.0:subcategory:GV.SC-03`: GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes

**Deterministic results**

schema_valid=pass, citation_ids_valid=pass, citations_in_bundle=pass, abstention_correct=pass, mapping_pairs_official=pass, mapping_cites_matching_row=pass, versions_correct=pass, expected_rows_covered=n/a, expected_controls_referenced=pass, conflict_preserved=n/a, new_control_no_reference=n/a, no_forbidden_mappings=n/a, no_unsupported_removal=pass, no_uncited_claims=pass

**LLM judge**

- scores (1-5): faithfulness=5, answer_relevance=5, factual_correctness=5, completeness=5, citation_support=5
- judge: groq/openai/gpt-oss-120b; independence: Generator and judge are different model families (different model vendors) but are served by the SAME provider infrastructure (shared platform, API account and rate limits). Family-level bias is reduced, not removed, and the judge's opinion is still not ground truth; calibrate with human review.
- faithfulness units: {'S1': 'supported', 'K1': 'supported'} (non-factual: 0)

| Claim | Units | Evidence | Verdict | Justification |
|---|---|---|---|---|
| GV.SC-03 requires that cybersecurity supply chain risk management be integrated  | S1, K1 | chunk:csf2.0:subcategory:GV.SC-03 | supported | The evidence text explicitly states that GV.SC-03 integrates cybersecurity suppl |

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_

## B01 - What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

- Category: `comparison`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 22: GV.SC -> ID.SC [xwalk:row22]

**Gemini answer**

In CSF 1.1, supply chain risk management is primarily addressed under the Identify function with two subcategories: ID.SC-1 (processes identified and established) and ID.SC-2 (suppliers identified, prioritized, and assessed). In CSF 2.0, this focus is significantly expanded and restructured. A new category, Cybersecurity Supply Chain Risk Management (GV.SC), is introduced under the Govern function, containing multiple subcategories (GV.SC-01 through GV.SC-10) that cover program establishment, integration with enterprise risk management, supplier prioritization, due diligence, lifecycle monitoring, and post-contract activities. Additionally, CSF 2.0 includes GV.RM-05 for communication lines regarding supplier risks and ID.RA-10 for assessing critical suppliers prior to acquisition. The official crosswalk maps these new CSF 2.0 subcategories back to the two CSF 1.1 subcategories, indicating a shift from a limited identification focus to a comprehensive governance and lifecycle management approach.

- citations: ['chunk:csf1.1:subcategory:ID.SC-1', 'chunk:csf1.1:subcategory:ID.SC-2', 'chunk:csf2.0:subcategory:GV.RM-05', 'chunk:csf2.0:subcategory:GV.SC-01', 'chunk:csf2.0:subcategory:GV.SC-03', 'chunk:csf2.0:subcategory:GV.SC-04', 'chunk:csf2.0:subcategory:GV.SC-06', 'chunk:csf2.0:subcategory:GV.SC-07', 'chunk:csf2.0:subcategory:GV.SC-09', 'chunk:csf2.0:subcategory:GV.SC-10', 'chunk:csf2.0:subcategory:ID.RA-10', 'chunk:csf2.0:text:65a38d02bf94', 'xwalk:row19', 'xwalk:row23', 'xwalk:row25', 'xwalk:row27', 'xwalk:row29', 'xwalk:row30', 'xwalk:row33', 'xwalk:row34', 'xwalk:row77']
- mappings: [('GV.RM-05', 'ID.SC-1', ['xwalk:row19']), ('GV.SC-01', 'ID.SC-1', ['xwalk:row23']), ('GV.SC-03', 'ID.SC-2', ['xwalk:row25']), ('GV.SC-04', 'ID.SC-2', ['xwalk:row27']), ('GV.SC-06', 'ID.SC-1', ['xwalk:row29']), ('GV.SC-07', 'ID.SC-2', ['xwalk:row30']), ('GV.SC-09', 'ID.SC-1', ['xwalk:row33']), ('GV.SC-10', 'ID.SC-1', ['xwalk:row34']), ('ID.RA-10', 'ID.SC-2', ['xwalk:row77'])]

**Source evidence cited**

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
- `chunk:csf2.0:text:65a38d02bf94`: This appendix describes the Functions, Categories, and Subcategories of the CSF Core. Table 1 lists the CSF 2.0 Core Function and Category names and unique alphabetic identifiers. Each Function name in the table is linked to its portion of the appendix. The order of Functions, Categories, and Subcat
- `xwalk:row19`: GV.RM-05 -> ID.SC-1 [mapped]
- `xwalk:row23`: GV.SC-01 -> ID.SC-1 [mapped]
- `xwalk:row25`: GV.SC-03 -> ID.SC-2 [mapped]
- `xwalk:row27`: GV.SC-04 -> ID.SC-2 [mapped]
- `xwalk:row29`: GV.SC-06 -> ID.SC-1 [mapped]
- `xwalk:row30`: GV.SC-07 -> ID.SC-2 [mapped]
- `xwalk:row33`: GV.SC-09 -> ID.SC-1 [mapped]
- `xwalk:row34`: GV.SC-10 -> ID.SC-1 [mapped]
- `xwalk:row77`: ID.RA-10 -> ID.SC-2 [mapped]

**Deterministic results**

schema_valid=pass, citation_ids_valid=pass, citations_in_bundle=pass, abstention_correct=pass, mapping_pairs_official=pass, mapping_cites_matching_row=pass, versions_correct=pass, expected_rows_covered=fail, expected_controls_referenced=n/a, conflict_preserved=n/a, new_control_no_reference=n/a, no_forbidden_mappings=n/a, no_unsupported_removal=pass, no_uncited_claims=pass

**LLM judge**

_provider_error: provider_error: Groq returned HTTP 400 (json_validate_failed)_

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_

## C01 - How does GV.OC-01 map to CSF 1.1?

- Category: `official_mapping`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]
- Official row 5: GV.OC-01 -> ID.BE-3 [xwalk:row5]

**Gemini answer**

_No answer (not_attempted)._

**Source evidence cited**

_none_

**Deterministic results**

_not run_

**LLM judge**

_not run_

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_

## F01 - How does GV.SC-03 map to CSF 1.1?

- Category: `conflict`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 25: GV.SC-03 -> ID.SC-2 [xwalk:row25]
- Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]
- must preserve conflicting rows [25, 26]

**Gemini answer**

_No answer (not_attempted)._

**Source evidence cited**

_none_

**Deterministic results**

_not run_

**LLM judge**

_not run_

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_

## E01 - How does GV.OV-01 map to CSF 1.1?

- Category: `conceptually_new`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 46: GV.OV-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row46]

**Gemini answer**

_No answer (not_attempted)._

**Source evidence cited**

_none_

**Deterministic results**

_not run_

**LLM judge**

_not run_

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_

## H02 - Which CSF control requires quantum-safe cryptography?

- Category: `abstention`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- should abstain: The corpus has no cryptography content at all; any retrieved passage is off-topic.

**Gemini answer**

_No answer (not_attempted)._

**Source evidence cited**

_none_

**Deterministic results**

_not run_

**LLM judge**

_not run_

**Human review**

- Status: **pending**; reviewer: _(none)_
- faithfulness: PENDING
- answer_relevance: PENDING
- factual_correctness: PENDING
- completeness: PENDING
- citation_support: PENDING
- Judge/human disagreement notes: _(blank)_
- Reviewer notes: _(blank)_
