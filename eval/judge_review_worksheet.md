# Judge calibration worksheet

Edit `eval/judge_calibration.json` (not this file): set `status` to `reviewed`, add your name, give each of the five dimensions an integer 1-5 using the rubric in `eval/judge_report.md`, and record any disagreement with the LLM judge in `disagreement_notes`. **All human fields are currently pending unless shown otherwise.**

## A01 - What does GV.SC-03 require?

- Category: `exact_control`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- GV.SC-03 integrates supply chain risk management into broader risk processes. [chunk:csf2.0:subcategory:GV.SC-03] - "Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes"

**Gemini answer**

_Not generated (no live run)._

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

## B01 - What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

- Category: `comparison`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 22: GV.SC -> ID.SC [xwalk:row22]

**Gemini answer**

_Not generated (no live run)._

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

## C01 - How does GV.OC-01 map to CSF 1.1?

- Category: `official_mapping`; labels AI-curated, **not human-reviewed**

**Gold expected facts**

- Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]
- Official row 5: GV.OC-01 -> ID.BE-3 [xwalk:row5]

**Gemini answer**

_Not generated (no live run)._

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

_Not generated (no live run)._

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

_Not generated (no live run)._

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

_Not generated (no live run)._

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
