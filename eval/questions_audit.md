# Evaluation question audit sheet

**Label provenance:** every judgment below was written by an AI assistant (Claude) from the stored source text and, for cross-version pairs, the official NIST crosswalk rows. No retrieval output was used. **No human has reviewed these labels.** Grade 2 = highly relevant, grade 1 = relevant. `provisional` queries are excluded from headline metrics.

## E01 - GV.SC-03

- category: `exact_id`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:GV.SC-03` (CSF 2.0 GV.SC-03, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.SC-03)
  - why: The CSF 2.0 subcategory with exactly this ID.
  - source: "GV.SC-03: Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes"

## E02 - PR.AT-1

- category: `exact_id`  difficulty: `easy`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.AT-1` (CSF 1.1 PR.AT-1, nist_csf_1_1.pdf p.38, Core > Protect (PR) > PR.AT-1)
  - why: The CSF 1.1 subcategory PR.AT-1 (unpadded 1.1 spelling).
  - source: "PR.AT-1: All users are informed and trained"

## E03 - ID.AM-1

- category: `exact_id`  difficulty: `medium`  version filter: `none`  status: **final**  
- notes: Unfiltered ID query: both versions' controls carry this normalised ID.

- **grade 2** `csf1.1:subcategory:ID.AM-1` (CSF 1.1 ID.AM-1, nist_csf_1_1.pdf p.31, Core > Identify (ID) > ID.AM-1)
  - why: CSF 1.1 subcategory ID.AM-1 (physical devices inventoried).
  - source: "ID.AM-1: Physical devices and systems within the organization are inventoried"
- **grade 2** `csf2.0:subcategory:ID.AM-01` (CSF 2.0 ID.AM-01, nist_csf_2_0.pdf p.23, Core > Identify (ID) > ID.AM-01)
  - why: CSF 2.0 ID.AM-01 normalises to the same ID and the official crosswalk row 51 maps ID.AM-01 to ID.AM-1; no version was requested.
  - source: "ID.AM-01: Inventories of hardware managed by the organization are maintained"

## E04 - DE.CM-01

- category: `exact_id`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:DE.CM-01` (CSF 2.0 DE.CM-01, nist_csf_2_0.pdf p.26, Core > Detect (DE) > DE.CM-01)
  - why: The CSF 2.0 subcategory with exactly this ID.
  - source: "DE.CM-01: Networks and network services are monitored to find potentially adverse events"

## E05 - RS.MA-02

- category: `exact_id`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:RS.MA-02` (CSF 2.0 RS.MA-02, nist_csf_2_0.pdf p.27, Core > Respond (RS) > RS.MA-02)
  - why: The CSF 2.0 subcategory with exactly this ID (incident reports triaged).
  - source: "RS.MA-02: Incident reports are triaged and validated"

## E06 - PR.DS-10

- category: `exact_id`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:PR.DS-10` (CSF 2.0 PR.DS-10, nist_csf_2_0.pdf p.25, Core > Protect (PR) > PR.DS-10)
  - why: The CSF 2.0 subcategory PR.DS-10 (data-in-use). Number is not sequential.
  - source: "PR.DS-10: The confidentiality, integrity, and availability of data-in-use are protected"

## E07 - RC.RP-3

- category: `exact_id`  difficulty: `medium`  version filter: `2.0`  status: **final**  
- notes: ID spelling variant.

- **grade 2** `csf2.0:subcategory:RC.RP-03` (CSF 2.0 RC.RP-03, nist_csf_2_0.pdf p.28, Core > Recover (RC) > RC.RP-03)
  - why: User wrote the unpadded spelling; the 2.0 control is RC.RP-03.
  - source: "RC.RP-03: The integrity of backups and other restoration assets is verified before using them for restoration"

## E08 - ID.SC

- category: `exact_id`  difficulty: `medium`  version filter: `1.1`  status: **final**  
- notes: Category-level ID; its subcategories are plausible near-misses but not labelled.

- **grade 2** `csf1.1:category:ID.SC` (CSF 1.1 ID.SC, nist_csf_1_1.pdf p.35, Core > Identify (ID) > ID.SC)
  - why: The CSF 1.1 category chunk with this identifier.
  - source: "Supply Chain Risk Management (ID.SC): The organization’s priorities, constraints, risk tolerances, and assumptions are established and used to support risk deci"

## E09 - GV.OV

- category: `exact_id`  difficulty: `medium`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:category:GV.OV` (CSF 2.0 GV.OV, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.OV)
  - why: The CSF 2.0 Oversight category chunk with this identifier.
  - source: "Oversight (GV.OV): Results of organization-wide cybersecurity risk management activities and performance are used to inform, improve, and adjust the risk manage"

## E10 - DE.AE-5

- category: `exact_id`  difficulty: `easy`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:subcategory:DE.AE-5` (CSF 1.1 DE.AE-5, nist_csf_1_1.pdf p.45, Core > Detect (DE) > DE.AE-5)
  - why: The CSF 1.1 subcategory DE.AE-5 (incident alert thresholds).
  - source: "DE.AE-5: Incident alert thresholds are established"

## E11 - What does PR.AC-7 require?

- category: `exact_id`  difficulty: `medium`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.AC-7` (CSF 1.1 PR.AC-7, nist_csf_1_1.pdf p.37, Core > Protect (PR) > PR.AC-7)
  - why: ID embedded in a natural-language question; PR.AC-7 in CSF 1.1.
  - source: "PR.AC-7: Users, devices, and other assets are authenticated (e.g., single-factor, multi-factor) commensurate with the risk of the transaction (e.g., individuals"

## S01 - How should an organization protect data that is stored on disks and in databases?

- category: `semantic`  difficulty: `easy`  version filter: `none`  status: **final**  
- notes: Paraphrase of 'data at rest' without the term.

- **grade 2** `csf1.1:subcategory:PR.DS-1` (CSF 1.1 PR.DS-1, nist_csf_1_1.pdf p.39, Core > Protect (PR) > PR.DS-1)
  - why: PR.DS-1 'Data-at-rest is protected'.
  - source: "PR.DS-1: Data-at-rest is protected"
- **grade 2** `csf2.0:subcategory:PR.DS-01` (CSF 2.0 PR.DS-01, nist_csf_2_0.pdf p.25, Core > Protect (PR) > PR.DS-01)
  - why: PR.DS-01 protects confidentiality, integrity and availability of data-at-rest; crosswalk row 119 maps it to PR.DS-1.
  - source: "PR.DS-01: The confidentiality, integrity, and availability of data-at-rest are protected"

## S02 - Which outcome requires users and devices to be authenticated, for example with multi-factor authentication?

- category: `semantic`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.AC-7` (CSF 1.1 PR.AC-7, nist_csf_1_1.pdf p.37, Core > Protect (PR) > PR.AC-7)
  - why: States users, devices and assets are authenticated (e.g., single-factor, multi-factor).
  - source: "PR.AC-7: Users, devices, and other assets are authenticated (e.g., single-factor, multi-factor) commensurate with the risk of the transaction (e.g., individuals"
- **grade 1** `csf2.0:subcategory:PR.AA-03` (CSF 2.0 PR.AA-03, nist_csf_2_0.pdf p.24, Core > Protect (PR) > PR.AA-03)
  - why: 2.0 'Users, services, and hardware are authenticated'; no MFA wording, linked to PR.AC-7 by crosswalk row 103.
  - source: "PR.AA-03: Users, services, and hardware are authenticated"

## S03 - Backups should be created and checked regularly to make sure they can be restored.

- category: `semantic`  difficulty: `easy`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.IP-4` (CSF 1.1 PR.IP-4, nist_csf_1_1.pdf p.41, Core > Protect (PR) > PR.IP-4)
  - why: PR.IP-4 'Backups of information are conducted, maintained, and tested'.
  - source: "PR.IP-4: Backups of information are conducted, maintained, and tested"
- **grade 2** `csf2.0:subcategory:PR.DS-11` (CSF 2.0 PR.DS-11, nist_csf_2_0.pdf p.25, Core > Protect (PR) > PR.DS-11)
  - why: PR.DS-11 'Backups of data are created, protected, maintained, and tested'; crosswalk row 126.
  - source: "PR.DS-11: Backups of data are created, protected, maintained, and tested"

## S04 - Keeping an inventory of the physical computers and devices an organization owns

- category: `semantic`  difficulty: `easy`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.AM-1` (CSF 1.1 ID.AM-1, nist_csf_1_1.pdf p.31, Core > Identify (ID) > ID.AM-1)
  - why: ID.AM-1 'Physical devices and systems ... are inventoried'.
  - source: "ID.AM-1: Physical devices and systems within the organization are inventoried"
- **grade 2** `csf2.0:subcategory:ID.AM-01` (CSF 2.0 ID.AM-01, nist_csf_2_0.pdf p.23, Core > Identify (ID) > ID.AM-01)
  - why: ID.AM-01 'Inventories of hardware managed by the organization are maintained'.
  - source: "ID.AM-01: Inventories of hardware managed by the organization are maintained"

## S05 - How should an organization handle security weaknesses reported to it by outside researchers?

- category: `semantic`  difficulty: `medium`  version filter: `none`  status: **final**  
- notes: No lexical overlap with 'disclosure'.

- **grade 2** `csf1.1:subcategory:RS.AN-5` (CSF 1.1 RS.AN-5, nist_csf_1_1.pdf p.49, Core > Respond (RS) > RS.AN-5)
  - why: RS.AN-5 processes to receive, analyze and respond to vulnerabilities disclosed to the organization.
  - source: "RS.AN-5: Processes are established to receive, analyze and respond to vulnerabilities disclosed to the organization from internal and external sources (e.g. int"
- **grade 2** `csf2.0:subcategory:ID.RA-08` (CSF 2.0 ID.RA-08, nist_csf_2_0.pdf p.24, Core > Identify (ID) > ID.RA-08)
  - why: ID.RA-08 processes for receiving, analyzing and responding to vulnerability disclosures; crosswalk row 75.
  - source: "ID.RA-08: Processes for receiving, analyzing, and responding to vulnerability disclosures are established"

## S06 - Receiving cyber threat intelligence from information sharing groups

- category: `semantic`  difficulty: `easy`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.RA-2` (CSF 1.1 ID.RA-2, nist_csf_1_1.pdf p.33, Core > Identify (ID) > ID.RA-2)
  - why: ID.RA-2 threat intelligence from information sharing forums and sources.
  - source: "ID.RA-2: Cyber threat intelligence is received from information sharing forums and sources"
- **grade 2** `csf2.0:subcategory:ID.RA-02` (CSF 2.0 ID.RA-02, nist_csf_2_0.pdf p.24, Core > Identify (ID) > ID.RA-02)
  - why: ID.RA-02 same wording; crosswalk row 68.
  - source: "ID.RA-02: Cyber threat intelligence is received from information sharing forums and sources"

## S07 - Stopping a cybersecurity incident from spreading further

- category: `semantic`  difficulty: `easy`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:RS.MI-1` (CSF 1.1 RS.MI-1, nist_csf_1_1.pdf p.49, Core > Respond (RS) > RS.MI-1)
  - why: RS.MI-1 'Incidents are contained'.
  - source: "RS.MI-1: Incidents are contained"
- **grade 2** `csf2.0:subcategory:RS.MI-01` (CSF 2.0 RS.MI-01, nist_csf_2_0.pdf p.27, Core > Respond (RS) > RS.MI-01)
  - why: RS.MI-01 'Incidents are contained'; crosswalk row 193.
  - source: "RS.MI-01: Incidents are contained"

## S08 - How are response and recovery plans improved using lessons learned from incidents?

- category: `semantic`  difficulty: `hard`  version filter: `none`  status: **provisional**  
- notes: PROVISIONAL: several 2.0 controls are plausible and the grading of which counts is uncertain.

- **grade 2** `csf1.1:subcategory:RS.IM-1` (CSF 1.1 RS.IM-1, nist_csf_1_1.pdf p.50, Core > Respond (RS) > RS.IM-1)
  - why: RS.IM-1 'Response plans incorporate lessons learned'.
  - source: "RS.IM-1: Response plans incorporate lessons learned"
- **grade 2** `csf1.1:subcategory:RC.IM-1` (CSF 1.1 RC.IM-1, nist_csf_1_1.pdf p.50, Core > Recover (RC) > RC.IM-1)
  - why: RC.IM-1 'Recovery plans incorporate lessons learned'.
  - source: "RC.IM-1: Recovery plans incorporate lessons learned"
- **grade 1** `csf2.0:subcategory:ID.IM-04` (CSF 2.0 ID.IM-04, nist_csf_2_0.pdf p.24, Core > Identify (ID) > ID.IM-04)
  - why: ID.IM-04 plans ... maintained and improved; crosswalk rows 95-96 link RS.IM-1/RC.IM-1.
  - source: "ID.IM-04: Incident response plans and other cybersecurity plans that affect operations are established, communicated, maintained, and improved"
- **grade 1** `csf2.0:subcategory:ID.IM-03` (CSF 2.0 ID.IM-03, nist_csf_2_0.pdf p.24, Core > Identify (ID) > ID.IM-03)
  - why: ID.IM-03 improvements from operational activities; crosswalk rows 90, 92.
  - source: "ID.IM-03: Improvements are identified from execution of operational processes, procedures, and activities"

## S09 - What does the framework say about keeping audit trails and logs of system activity?

- category: `semantic`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.PT-1` (CSF 1.1 PR.PT-1, nist_csf_1_1.pdf p.43, Core > Protect (PR) > PR.PT-1)
  - why: PR.PT-1 audit/log records are determined, documented, implemented and reviewed.
  - source: "PR.PT-1: Audit/log records are determined, documented, implemented, and reviewed in accordance with policy"
- **grade 2** `csf2.0:subcategory:PR.PS-04` (CSF 2.0 PR.PS-04, nist_csf_2_0.pdf p.25, Core > Protect (PR) > PR.PS-04)
  - why: PR.PS-04 log records are generated and made available for continuous monitoring; crosswalk row 136.
  - source: "PR.PS-04: Log records are generated and made available for continuous monitoring"

## S10 - Development and testing systems should be kept apart from live production systems.

- category: `semantic`  difficulty: `hard`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.DS-7` (CSF 1.1 PR.DS-7, nist_csf_1_1.pdf p.40, Core > Protect (PR) > PR.DS-7)
  - why: PR.DS-7 'development and testing environment(s) are separate from the production environment'.
  - source: "PR.DS-7: The development and testing environment(s) are separate from the production environment"
- **grade 1** `csf2.0:subcategory:PR.IR-01` (CSF 2.0 PR.IR-01, nist_csf_2_0.pdf p.25, Core > Protect (PR) > PR.IR-01)
  - why: PR.IR-01 protects networks and environments; crosswalk row 142 maps PR.DS-7 here, but no explicit separation wording.
  - source: "PR.IR-01: Networks and environments are protected from unauthorized logical access and usage"

## V01 - Which outcome covers reviewing the risk management strategy to make sure it still covers the organization's requirements and risks?

- category: `version_specific`  difficulty: `medium`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:GV.OV-02` (CSF 2.0 GV.OV-02, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.OV-02)
  - why: GV.OV-02 strategy 'reviewed and adjusted to ensure coverage of organizational requirements and risks'.
  - source: "GV.OV-02: The cybersecurity risk management strategy is reviewed and adjusted to ensure coverage of organizational requirements and risks"
- **grade 1** `csf2.0:subcategory:GV.OV-01` (CSF 2.0 GV.OV-01, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.OV-01)
  - why: GV.OV-01 strategy outcomes reviewed to inform and adjust strategy.
  - source: "GV.OV-01: Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction"
- **grade 1** `csf2.0:subcategory:GV.OV-03` (CSF 2.0 GV.OV-03, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.OV-03)
  - why: GV.OV-03 performance evaluated and reviewed for needed adjustments.
  - source: "GV.OV-03: Organizational cybersecurity risk management performance is evaluated and reviewed for adjustments needed"

## V02 - Who is accountable for cybersecurity risk and builds a risk-aware culture?

- category: `version_specific`  difficulty: `medium`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:GV.RR-01` (CSF 2.0 GV.RR-01, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.RR-01)
  - why: GV.RR-01 organizational leadership is responsible and accountable and fosters a risk-aware culture.
  - source: "GV.RR-01: Organizational leadership is responsible and accountable for cybersecurity risk and fosters a culture that is risk-aware, ethical, and continually imp"

## V03 - What is the purpose of the GOVERN function?

- category: `version_specific`  difficulty: `medium`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:text:0105534cd143` (CSF 2.0, nist_csf_2_0.pdf p.8, 2. Introduction to the CSF Core)
  - why: Narrative defining GOVERN (GV) and what the Function provides.
  - source: "• GOVERN (GV) — The organization’s cybersecurity risk management strategy, expectations, and policy are established, communicated, and monitored. The GOVERN Fun"
- **grade 2** `csf2.0:function:GV` (CSF 2.0 GV, nist_csf_2_0.pdf p.21, Core > Govern (GV))
  - why: Function chunk 'GOVERN (GV): ... strategy, expectations, and policy are established, communicated, and monitored'.
  - source: "GOVERN (GV): The organization’s cybersecurity risk management strategy, expectations, and policy are established, communicated, and monitored"
- **grade 1** `csf2.0:text:00c7e5b2ba7b` (CSF 2.0, nist_csf_2_0.pdf p.16, 5. Improving Cybersecurity Risk Communication and Integration > 5.1. Improving Risk Management Communication)
  - why: Explains how the GOVERN Function supports risk communication with executives.
  - source: "The GOVERN Function supports organizational risk communication with executives. Executives’ discussions involve strategy, particularly how cybersecurity-related"

## V04 - What are the six Functions of the CSF Core?

- category: `version_specific`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:text:2400d2aa8dcf` (CSF 2.0, nist_csf_2_0.pdf p.8, 2. Introduction to the CSF Core)
  - why: Lists 'GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, and RECOVER' (verified by substring).
  - source: "Appendix A is the CSF Core — a set of cybersecurity outcomes arranged by Function, then Category, and finally Subcategory, as depicted in Fig. 1. These outcomes"
- **grade 1** `csf2.0:text:8962e17152b8` (CSF 2.0, nist_csf_2_0.pdf p.31, Appendix C. Glossary)
  - why: Glossary chunk that also lists the six Functions.
  - source: "CSF Category A group of related cybersecurity outcomes that collectively comprise a CSF Function. CSF Community Profile A baseline of CSF outcomes that is creat"

## V05 - What are the five Functions of the Framework Core?

- category: `version_specific`  difficulty: `easy`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:text:b1fe485caf83` (CSF 1.1, nist_csf_1_1.pdf p.13, 2.0 Framework Basics > 2.1 Framework Core)
  - why: Section 2.1 states the Functions: Identify, Protect, Detect, Respond, and Recover (verified by substring).
  - source: "The Framework Core provides a set of activities to achieve specific cybersecurity outcomes, and references examples of guidance to achieve those outcomes. The C"
- **grade 1** `csf1.1:text:d1930b34ffdb` (CSF 1.1, nist_csf_1_1.pdf p.20, 3.0 How to Use the Framework > 3.1 Basic Review of Cybersecurity Practices)
  - why: Section 3.1 repeats the five Functions.
  - source: "The Framework can be used to compare an organization’s current cybersecurity activities with those outlined in the Framework Core. Through the creation of a Cur"
- **grade 1** `csf1.1:text:dddb82324e42` (CSF 1.1, nist_csf_1_1.pdf p.52, Appendix B: Glossary)
  - why: Glossary entry listing the five Functions.
  - source: "Framework Core A set of cybersecurity activities and references that are common across critical infrastructure sectors and are organized around particular outco"

## V06 - How does the Framework describe the Implementation Tiers?

- category: `version_specific`  difficulty: `medium`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:text:28bf886ec726` (CSF 1.1, nist_csf_1_1.pdf p.15, 2.0 Framework Basics > 2.2 Framework Implementation Tiers)
  - why: Defines Tiers from Partial (Tier 1) to Adaptive (Tier 4).
  - source: "The Framework Implementation Tiers (“Tiers”) provide context on how an organization views cybersecurity risk and the processes in place to manage that risk. Ran"
- **grade 1** `csf1.1:text:4cd53030c0a8` (CSF 1.1, nist_csf_1_1.pdf p.15, 2.0 Framework Basics > 2.2 Framework Implementation Tiers)
  - why: Describes the Tier selection process.
  - source: "The Tier selection process considers an organization’s current risk management practices, threat environment, legal and regulatory requirements, information sha"

## V07 - What is a Community Profile?

- category: `version_specific`  difficulty: `easy`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:text:1e8b583f99d6` (CSF 2.0, nist_csf_2_0.pdf p.11, 3. Introduction to CSF Profiles and Tiers > 3.1. CSF Profiles)
  - why: Defines a Community Profile as a baseline of CSF outcomes for shared interests.
  - source: "A Community Profile is a baseline of CSF outcomes that is created and published to address shared interests and goals among a number of organizations. A Communi"
- **grade 1** `csf2.0:text:8962e17152b8` (CSF 2.0, nist_csf_2_0.pdf p.31, Appendix C. Glossary)
  - why: Glossary chunk containing the Community Profile definition.
  - source: "CSF Category A group of related cybersecurity outcomes that collectively comprise a CSF Function. CSF Community Profile A baseline of CSF outcomes that is creat"

## V08 - How does the CSF relate to artificial intelligence risks?

- category: `version_specific`  difficulty: `medium`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:text:752c4811c287` (CSF 2.0, nist_csf_2_0.pdf p.19, 5. Improving Cybersecurity Risk Communication and Integration > 5.2. Improving Integration with Other Risk Management Programs)
  - why: Bullet on risks from emerging technologies, AI and the NIST AI RMF.
  - source: "• Risks from emerging technologies: As new technologies and new applications of technology become available, new risks become clear. A contemporary example is a"
- **grade 1** `csf2.0:text:ce65b06e28e0` (CSF 2.0, nist_csf_2_0.pdf p.16, 5. Improving Cybersecurity Risk Communication and Integration > 5.2. Improving Integration with Other Risk Management Programs)
  - why: Lists AI among the ICT risks addressed alongside enterprise risk management.
  - source: "Every organization faces numerous types of ICT risk (e.g., privacy, supply chain, artificial intelligence) and may use frameworks and management tools that are "

## V09 - What methodology does the Framework describe for protecting privacy and civil liberties?

- category: `version_specific`  difficulty: `hard`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:text:c892f6549390` (CSF 1.1, nist_csf_1_1.pdf p.25, 3.0 How to Use the Framework > 3.6 Methodology to Protect Privacy and Civil Liberties)
  - why: Introduces the privacy and civil liberties methodology.
  - source: "This section describes a methodology to address individual privacy and civil liberties implications that may result from cybersecurity. This methodology is inte"
- **grade 2** `csf1.1:text:c8cf37e0d42a` (CSF 1.1, nist_csf_1_1.pdf p.25, 3.0 How to Use the Framework > 3.6 Methodology to Protect Privacy and Civil Liberties)
  - why: Privacy principles to incorporate (data minimization, etc.).
  - source: "The government and its agents have a responsibility to protect civil liberties arising from cybersecurity activities. As referenced in the methodology below, go"
- **grade 1** `csf1.1:text:11c75e8ed0b8` (CSF 1.1, nist_csf_1_1.pdf p.26, 3.0 How to Use the Framework > 3.6 Methodology to Protect Privacy and Civil Liberties)
  - why: Continues the methodology bullets (privacy responsibilities, compliance processes).
  - source: "• Individuals with cybersecurity-related privacy responsibilities report to appropriate management and are appropriately trained. • Process is in place to suppo"

## V10 - Which outcome sets post-incident operating norms based on critical mission functions?

- category: `version_specific`  difficulty: `hard`  version filter: `2.0`  status: **final**

- **grade 2** `csf2.0:subcategory:RC.RP-04` (CSF 2.0 RC.RP-04, nist_csf_2_0.pdf p.28, Core > Recover (RC) > RC.RP-04)
  - why: RC.RP-04 'Critical mission functions and cybersecurity risk management are considered to establish post-incident operational norms'.
  - source: "RC.RP-04: Critical mission functions and cybersecurity risk management are considered to establish post-incident operational norms"

## V11 - How can a Target Profile help with decisions about buying products and services?

- category: `version_specific`  difficulty: `medium`  version filter: `1.1`  status: **final**

- **grade 2** `csf1.1:text:4aaca68a5ca1` (CSF 1.1, nist_csf_1_1.pdf p.25, 3.0 How to Use the Framework > 3.4 Buying Decisions)
  - why: Section 3.4 Buying Decisions: Target Profiles inform buying decisions.
  - source: "Since a Framework Target Profile is a prioritized list of organizational cybersecurity requirements, Target Profiles can be used to inform decisions about buyin"

## X01 - proofing identities and binding them to credentials

- category: `cross_version`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:PR.AC-6` (CSF 1.1 PR.AC-6, nist_csf_1_1.pdf p.37, Core > Protect (PR) > PR.AC-6)
  - why: PR.AC-6 identities proofed and bound to credentials.
  - source: "PR.AC-6: Identities are proofed and bound to credentials and asserted in interactions"
- **grade 2** `csf2.0:subcategory:PR.AA-02` (CSF 2.0 PR.AA-02, nist_csf_2_0.pdf p.24, Core > Protect (PR) > PR.AA-02)
  - why: PR.AA-02 same outcome, 2.0 wording; crosswalk row 101.
  - source: "PR.AA-02: Identities are proofed and bound to credentials based on the context of interactions"

## X02 - executing the recovery plan during or after a cybersecurity incident

- category: `cross_version`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:RC.RP-1` (CSF 1.1 RC.RP-1, nist_csf_1_1.pdf p.50, Core > Recover (RC) > RC.RP-1)
  - why: RC.RP-1 recovery plan is executed during or after an incident.
  - source: "RC.RP-1: Recovery plan is executed during or after a cybersecurity incident"
- **grade 2** `csf2.0:subcategory:RC.RP-01` (CSF 2.0 RC.RP-01, nist_csf_2_0.pdf p.27, Core > Recover (RC) > RC.RP-01)
  - why: RC.RP-01 recovery portion of the IR plan is executed; crosswalk row 197.
  - source: "RC.RP-01: The recovery portion of the incident response plan is executed once initiated from the incident response process"

## X03 - knowing which suppliers matter most and ranking them by how critical they are

- category: `cross_version`  difficulty: `hard`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.SC-2` (CSF 1.1 ID.SC-2, nist_csf_1_1.pdf p.35, Core > Identify (ID) > ID.SC-2)
  - why: ID.SC-2 suppliers and third parties identified, prioritized and assessed.
  - source: "ID.SC-2: Suppliers and third party partners of information systems, components, and services are identified, prioritized, and assessed using a cyber supply chai"
- **grade 2** `csf2.0:subcategory:GV.SC-04` (CSF 2.0 GV.SC-04, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.SC-04)
  - why: GV.SC-04 'Suppliers are known and prioritized by criticality'; crosswalk row 27.
  - source: "GV.SC-04: Suppliers are known and prioritized by criticality"

## X04 - risk tolerance and risk appetite statements

- category: `cross_version`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.RM-2` (CSF 1.1 ID.RM-2, nist_csf_1_1.pdf p.34, Core > Identify (ID) > ID.RM-2)
  - why: ID.RM-2 organizational risk tolerance is determined and clearly expressed.
  - source: "ID.RM-2: Organizational risk tolerance is determined and clearly expressed"
- **grade 2** `csf2.0:subcategory:GV.RM-02` (CSF 2.0 GV.RM-02, nist_csf_2_0.pdf p.21, Core > Govern (GV) > GV.RM-02)
  - why: GV.RM-02 risk appetite and risk tolerance statements; crosswalk row 15.
  - source: "GV.RM-02: Risk appetite and risk tolerance statements are established, communicated, and maintained"

## X05 - cybersecurity responsibilities of the whole workforce and outside partners

- category: `cross_version`  difficulty: `hard`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.AM-6` (CSF 1.1 ID.AM-6, nist_csf_1_1.pdf p.31, Core > Identify (ID) > ID.AM-6)
  - why: ID.AM-6 roles and responsibilities for the entire workforce and third-party stakeholders.
  - source: "ID.AM-6: Cybersecurity roles and responsibilities for the entire workforce and third-party stakeholders (e.g., suppliers, customers, partners) are established"
- **grade 2** `csf2.0:subcategory:GV.RR-02` (CSF 2.0 GV.RR-02, nist_csf_2_0.pdf p.22, Core > Govern (GV) > GV.RR-02)
  - why: GV.RR-02 roles, responsibilities and authorities established; crosswalk row 37 maps ID.AM-6 here.
  - source: "GV.RR-02: Roles, responsibilities, and authorities related to cybersecurity risk management are established, communicated, understood, and enforced"

## X06 - legal and regulatory obligations including privacy and civil liberties

- category: `cross_version`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:ID.GV-3` (CSF 1.1 ID.GV-3, nist_csf_1_1.pdf p.33, Core > Identify (ID) > ID.GV-3)
  - why: ID.GV-3 legal and regulatory requirements incl. privacy and civil liberties.
  - source: "ID.GV-3: Legal and regulatory requirements regarding cybersecurity, including privacy and civil liberties obligations, are understood and managed"
- **grade 2** `csf2.0:subcategory:GV.OC-03` (CSF 2.0 GV.OC-03, nist_csf_2_0.pdf p.21, Core > Govern (GV) > GV.OC-03)
  - why: GV.OC-03 legal, regulatory and contractual requirements incl. privacy and civil liberties; crosswalk row 8.
  - source: "GV.OC-03: Legal, regulatory, and contractual requirements regarding cybersecurity — including privacy and civil liberties obligations — are understood and manag"

## X07 - collecting and correlating event data from several sources

- category: `cross_version`  difficulty: `medium`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:subcategory:DE.AE-3` (CSF 1.1 DE.AE-3, nist_csf_1_1.pdf p.45, Core > Detect (DE) > DE.AE-3)
  - why: DE.AE-3 event data collected and correlated from multiple sources and sensors.
  - source: "DE.AE-3: Event data are collected and correlated from multiple sources and sensors"
- **grade 2** `csf2.0:subcategory:DE.AE-03` (CSF 2.0 DE.AE-03, nist_csf_2_0.pdf p.26, Core > Detect (DE) > DE.AE-03)
  - why: DE.AE-03 information is correlated from multiple sources; crosswalk row 166.
  - source: "DE.AE-03: Information is correlated from multiple sources"

## X08 - What are the Tier levels and their names?

- category: `cross_version`  difficulty: `hard`  version filter: `none`  status: **final**

- **grade 2** `csf1.1:text:28bf886ec726` (CSF 1.1, nist_csf_1_1.pdf p.15, 2.0 Framework Basics > 2.2 Framework Implementation Tiers)
  - why: CSF 1.1 Tiers from Partial (Tier 1) to Adaptive (Tier 4).
  - source: "The Framework Implementation Tiers (“Tiers”) provide context on how an organization views cybersecurity risk and the processes in place to manage that risk. Ran"
- **grade 2** `csf2.0:text:6a6b15d78865` (CSF 2.0, nist_csf_2_0.pdf p.12, 3. Introduction to CSF Profiles and Tiers > 3.2. CSF Tiers)
  - why: CSF 2.0 Tiers: Partial, Risk Informed, Repeatable, Adaptive.
  - source: "An organization can choose to use the Tiers to inform its Current and Target Profiles. Tiers characterize the rigor of an organization’s cybersecurity risk gove"
