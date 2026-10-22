# Answer review worksheet

Reviewer instructions: for each question read the expected facts and the cited evidence, then edit `eval/answer_review.json` (not this file). `groundedness` ∈ ['grounded', 'partially_grounded', 'not_grounded']; `completeness` ∈ ['complete', 'partial', 'incomplete']; set `status` to `reviewed` and add your name. Leave `pending` if you have not examined the answer. **All scores are currently pending.**

## A01 - What does GV.SC-03 require?

- Category: `exact_control`  |  Expected query type: `single_version`  |  Allowed versions: 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.SC-03` (CSF 2.0)
- fact: GV.SC-03 integrates supply chain risk management into broader risk processes. [chunk:csf2.0:subcategory:GV.SC-03] - "Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes"

**Evidence the pipeline assembled (offline)**

- query type `single_version`; searched ['2.0']; controls ['GV.SC-03@2.0']; crosswalk rows []; passages 4; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## A02 - What does PR.AT-1 require in CSF 1.1?

- Category: `exact_control`  |  Expected query type: `single_version`  |  Allowed versions: 1.1
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `PR.AT-1` (CSF 1.1)
- fact: CSF 1.1 PR.AT-1: all users are informed and trained. [chunk:csf1.1:subcategory:PR.AT-1] - "All users are informed and trained"

**Evidence the pipeline assembled (offline)**

- query type `single_version`; searched ['1.1']; controls ['PR.AT-1@1.1']; crosswalk rows []; passages 4; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## A03 - Explain DE.CM-01

- Category: `exact_control`  |  Expected query type: `single_version`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `DE.CM-01` (CSF 2.0)
- control `DE.CM-1` (CSF 1.1)
- fact: CSF 2.0 DE.CM-01 monitors networks and network services. [chunk:csf2.0:subcategory:DE.CM-01] - "Networks and network services are monitored to find potentially adverse events"
- fact: CSF 1.1 DE.CM-1 monitors the network. [chunk:csf1.1:subcategory:DE.CM-1] - "The network is monitored to detect potential cybersecurity events"

**Evidence the pipeline assembled (offline)**

- query type `single_version`; searched ['1.1', '2.0']; controls ['DE.CM-1@1.1', 'DE.CM-01@2.0']; crosswalk rows []; passages 8; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=pass, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## B01 - What are the differences between CSF 1.1 and 2.0 for supply chain risk management?

- Category: `comparison`  |  Expected query type: `cross_version_comparison`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- fact: Official row 22: GV.SC -> ID.SC [xwalk:row22]

**Evidence the pipeline assembled (offline)**

- query type `cross_version_comparison`; searched ['1.1', '2.0']; controls ['ID.SC@1.1', 'GV.SC@2.0', 'ID.SC-1@1.1', 'GV.RM-05@2.0', 'GV.SC-01@2.0', 'GV.SC-06@2.0', 'GV.SC-09@2.0', 'GV.SC-10@2.0', 'GV.SC-03@2.0', 'ID.SC-2@1.1']; crosswalk rows [19, 22, 23, 25, 26, 29, 33, 34]; passages 10; conflicts ['GV.SC-03']; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## B02 - Compare CSF 1.1 and 2.0 on risk tolerance and risk appetite statements

- Category: `comparison`  |  Expected query type: `cross_version_comparison`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- fact: Official row 15: GV.RM-02 -> ID.RM-2 [xwalk:row15]
- fact: Official row 16: GV.RM-02 -> ID.RM-3 [xwalk:row16]

**Evidence the pipeline assembled (offline)**

- query type `cross_version_comparison`; searched ['1.1', '2.0']; controls ['GV.RM-02@2.0', 'ID.RM-2@1.1', 'ID.RM-3@1.1', 'GV.RM@2.0', 'ID.RM@1.1']; crosswalk rows [13, 15, 16]; passages 10; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## B03 - What is new in CSF 2.0?

- Category: `comparison`  |  Expected query type: `cross_version_comparison`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- fact: Official row 21: GV.RM-07 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row21]
- fact: Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]
- fact: Official row 36: GV.RR-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row36]
- fact: Official row 45: GV.OV -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row45]
- fact: Official row 46: GV.OV-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row46]
- fact: Official row 47: GV.OV-02 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row47]
- fact: Official row 48: GV.OV-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row48]
- fact: Official row 57: ID.AM-07 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row57]
- fact: Official row 83: ID.IM-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row83]
- fact: Official row 104: PR.AA-04 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row104]
- fact: Official row 127: PR.PS -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row127]
- fact: Official row 137: PR.PS-05 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row137]
- fact: Official row 139: PR.IR -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row139]
- fact: Official row 181: RS.MA-05 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row181]
- fact: Official row 185: RS.AN-07 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row185]
- fact: Official row 186: RS.AN-08 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row186]
- fact: Official row 199: RC.RP-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row199]
- fact: Official row 200: RC.RP-04 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row200]
- fact: Official row 201: RC.RP-05 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row201]
- fact: Official row 202: RC.RP-06 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row202]

**Evidence the pipeline assembled (offline)**

- query type `cross_version_comparison`; searched ['1.1', '2.0']; controls []; crosswalk rows [21, 26, 36, 45, 46, 47, 48, 57, 83, 104, 127, 137, 139, 181, 185, 186, 199, 200, 201, 202]; passages 10; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## C01 - How does GV.OC-01 map to CSF 1.1?

- Category: `official_mapping`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.OC-01` (CSF 2.0)
- control `ID.BE-2` (CSF 1.1)
- control `ID.BE-3` (CSF 1.1)
- fact: Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]
- fact: Official row 5: GV.OC-01 -> ID.BE-3 [xwalk:row5]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['GV.OC-01@2.0', 'ID.BE-2@1.1', 'ID.BE-3@1.1']; crosswalk rows [4, 5]; passages 5; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## C02 - Which CSF 2.0 controls correspond to ID.BE-2?

- Category: `official_mapping`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `ID.BE-2` (CSF 1.1)
- control `GV.OC-01` (CSF 2.0)
- fact: Official row 4: GV.OC-01 -> ID.BE-2 [xwalk:row4]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['ID.BE-2@1.1', 'GV.OC-01@2.0']; crosswalk rows [4]; passages 5; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## C03 - How does PR.DS-01 map to CSF 1.1?

- Category: `official_mapping`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `PR.DS-01` (CSF 2.0)
- control `PR.DS-1` (CSF 1.1)
- fact: Official row 119: PR.DS-01 -> PR.DS-1 [xwalk:row119]
- fact: Official row 120: PR.DS-01 -> PR.DS-5 [xwalk:row120]
- fact: Official row 121: PR.DS-01 -> PR.DS-6 [xwalk:row121]
- fact: Official row 122: PR.DS-01 -> PR.PT-2 [xwalk:row122]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['PR.DS-1@1.1', 'PR.DS-01@2.0', 'PR.DS-5@1.1', 'PR.DS-6@1.1', 'PR.PT-2@1.1']; crosswalk rows [119, 120, 121, 122]; passages 5; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## D01 - Which CSF 1.1 controls does GV.RR-02 map to?

- Category: `one_to_many`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.RR-02` (CSF 2.0)
- control `ID.AM-6` (CSF 1.1)
- fact: Official row 37: GV.RR-02 -> ID.AM-6 [xwalk:row37]
- fact: Official row 38: GV.RR-02 -> ID.GV-2 [xwalk:row38]
- fact: Official row 39: GV.RR-02 -> DE.DP-1 [xwalk:row39]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['GV.RR-02@2.0', 'ID.AM-6@1.1', 'ID.GV-2@1.1', 'DE.DP-1@1.1']; crosswalk rows [37, 38, 39]; passages 5; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## D02 - Which CSF 2.0 controls correspond to ID.SC-1?

- Category: `one_to_many`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `ID.SC-1` (CSF 1.1)
- fact: Official row 19: GV.RM-05 -> ID.SC-1 [xwalk:row19]
- fact: Official row 23: GV.SC-01 -> ID.SC-1 [xwalk:row23]
- fact: Official row 29: GV.SC-06 -> ID.SC-1 [xwalk:row29]
- fact: Official row 33: GV.SC-09 -> ID.SC-1 [xwalk:row33]
- fact: Official row 34: GV.SC-10 -> ID.SC-1 [xwalk:row34]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['ID.SC-1@1.1', 'GV.RM-05@2.0', 'GV.SC-01@2.0', 'GV.SC-06@2.0', 'GV.SC-09@2.0', 'GV.SC-10@2.0']; crosswalk rows [19, 23, 29, 33, 34]; passages 5; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## E01 - How does GV.OV-01 map to CSF 1.1?

- Category: `conceptually_new`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.OV-01` (CSF 2.0)
- fact: Official row 46: GV.OV-01 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row46]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['GV.OV-01@2.0']; crosswalk rows [46]; passages 5; conflicts []; unmapped ['GV.OV-01']; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=pass, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## E02 - How does RC.RP-04 map to CSF 1.1?

- Category: `conceptually_new`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `RC.RP-04` (CSF 2.0)
- fact: Official row 200: RC.RP-04 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row200]

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['RC.RP-04@2.0']; crosswalk rows [200]; passages 5; conflicts []; unmapped ['RC.RP-04']; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=n/a, unmapped_flagged=pass, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## F01 - How does GV.SC-03 map to CSF 1.1?

- Category: `conflict`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.SC-03` (CSF 2.0)
- control `ID.SC-2` (CSF 1.1)
- fact: Official row 25: GV.SC-03 -> ID.SC-2 [xwalk:row25]
- fact: Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]
- must preserve conflicting rows [25, 26] (do not choose one)

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['GV.SC-03@2.0', 'ID.SC-2@1.1']; crosswalk rows [25, 26]; passages 5; conflicts ['GV.SC-03']; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=pass, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## F02 - Does GV.SC-03 have an equivalent in CSF 1.1?

- Category: `conflict`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `GV.SC-03` (CSF 2.0)
- control `ID.SC-2` (CSF 1.1)
- fact: Official row 25: GV.SC-03 -> ID.SC-2 [xwalk:row25]
- fact: Official row 26: GV.SC-03 -> no CSF 1.1 reference (conceptually new in 2.0) [xwalk:row26]
- must preserve conflicting rows [25, 26] (do not choose one)

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['GV.SC-03@2.0', 'ID.SC-2@1.1']; crosswalk rows [25, 26]; passages 5; conflicts ['GV.SC-03']; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=pass, conflict_surfaced=pass, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## G01 - How does RC.CO-2 map to CSF 2.0?

- Category: `missing_mapping`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**

**Expected evidence and facts**

- control `RC.CO-2` (CSF 1.1)
- fact: RC.CO-2 exists in CSF 1.1. [chunk:csf1.1:subcategory:RC.CO-2] - "Reputation is repaired after an incident"
- must NOT claim a mapping or removal for ['RC.CO-2']

**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls ['RC.CO-2@1.1']; crosswalk rows []; passages 5; conflicts []; unmapped ['RC.CO-2']; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=pass, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## H01 - What replaced GV.XX-99 in CSF 2.0?

- Category: `abstention`  |  Expected query type: `control_mapping`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**
- **Should abstain** (control_not_found): The control ID GV.XX-99 does not exist in either version.

**Expected evidence and facts**


**Evidence the pipeline assembled (offline)**

- query type `control_mapping`; searched ['1.1', '2.0']; controls []; crosswalk rows []; passages 6; conflicts []; unmapped []; missing ['control_not_found']
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=pass

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## H02 - Which CSF control requires quantum-safe cryptography?

- Category: `abstention`  |  Expected query type: `single_version`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**
- **Should abstain** (topic_absent): The corpus has no cryptography content at all; any retrieved passage is off-topic.
- Why abstention is justified: Not just the word 'quantum': the stored NIST text never mentions cryptography, encryption or any cryptographic algorithm in either version (0 chunks for each term), so no passage can say which control requires quantum-safe cryptography.

**Expected evidence and facts**


**Evidence the pipeline assembled (offline)**

- query type `single_version`; searched ['1.1', '2.0']; controls []; crosswalk rows []; passages 10; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## H03 - What is the penalty for failing to implement GV.SC-03?

- Category: `abstention`  |  Expected query type: `single_version`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**
- **Should abstain** (topic_absent): The question presumes a penalty regime that the documents do not contain.
- Why abstention is justified: GV.SC-03 exists (its text is in the evidence) but neither CSF document states any penalty, sanction or consequence for non-implementation (0 chunks for each concept term). The nearest passages (CSF 1.1 remarks on 'compliance' and that the Framework is voluntary) were read and do not define penalties. A reply that says the documents define no penalty is a legitimate alternative to a flat abstention; the automatic check is deliberately strict (see notes).

**Expected evidence and facts**

- control `GV.SC-03` (CSF 2.0)

**Evidence the pipeline assembled (offline)**

- query type `single_version`; searched ['2.0']; controls ['GV.SC-03@2.0']; crosswalk rows []; passages 4; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=pass, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, missing_evidence_reported=n/a

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**

## H04 - (blank question)

- Category: `invalid_input`  |  Expected query type: `unsupported`  |  Allowed versions: 1.1, 2.0
- Labels: AI-curated, source-checked, **not human-reviewed**
- **Invalid input**: the API must reject this with HTTP 422 (no retrieval, no model call). A blank question is invalid input: the API answers HTTP 422 and never retrieves or generates. It is NOT an evidence-based abstention.

**Expected evidence and facts**


**Evidence the pipeline assembled (offline)**

- query type `unsupported`; searched []; controls []; crosswalk rows []; passages 0; conflicts []; unmapped []; missing []
- evidence checks: query_type=pass, expected_controls_present=n/a, expected_rows_present=n/a, conflict_surfaced=n/a, unmapped_flagged=n/a, expected_uncertainty_surfaced=n/a, version_isolation=pass, bundle_citations_structurally_valid=pass, rejected_as_invalid_request=pass, defence_in_depth_if_reached=pass

**Generated answer**

_Not generated - offline mode (no model was called)._

**Review**

- Groundedness: PENDING
- Completeness: PENDING
- Reviewer notes: _(blank)_
- Reviewer: _(none)_
- Human review status: **pending**
