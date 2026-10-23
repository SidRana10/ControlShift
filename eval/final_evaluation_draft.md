# ControlShift — evaluation summary (DRAFT — PENDING HUMAN VERIFICATION)

> **Superseded by `eval/final_evaluation_report.md`** (phase closed with documented limitations; no independent human sign-off). Kept for traceability.

> **DRAFT — PENDING HUMAN VERIFICATION.** Nothing here is independently human-verified. Four kinds of statement are kept apart throughout:
> **[M]** machine verification (deterministic code); **[J]** LLM-judge assessment (Groq `openai/gpt-oss-120b`); **[AI]** AI-assisted source review (the preliminary
> per-question reading in `eval/human_review_packet.md`); **[H]** developer/human confirmation — **none exists yet** (see `eval/human_verification_checklist.md`). Six questions are a small exploratory sample and do **not**
> establish general RAG accuracy. No agreement between judge and human reviewers can be claimed until a human has actually reviewed the answers.

## 1. Project and evaluation overview
ControlShift is a version-aware RAG system over NIST CSF 1.1 and 2.0: ingestion into SQLite + indexes, query planning, structured lookups, hybrid retrieval, evidence assembly with
structural citation validation, grounded generation, and a FastAPI service. Answer quality was evaluated on six live questions with **Groq `qwen/qwen3.8-27b` as generator**
(Gemini repeatedly returned HTTP 503; Mistral returned 429) and **Groq `openai/gpt-oss-120b` as LLM judge**. The two models are different families but share Groq's infrastructure,
account and rate limits, so correlated errors are reduced, not removed. The retrieval benchmark (section 2) is a separate, earlier measurement and is not mixed with the answer results.

## 2. Dataset scope and limitations
- **Retrieval benchmark (separate; `eval/report.md`, unchanged):** 39 final questions over 384 chunks; hybrid + cross-encoder reached nDCG@5 0.848, MRR@10 0.905, Hit@5 0.974 (BM25: 0.780 / 0.836 / 0.897). Labels are AI-curated and not human-reviewed. These numbers describe ranking of chunks only, not answer quality.
- **Answer evaluation:** a gold set of 19 valid questions exists (`eval/answer_questions.jsonl`, AI-curated, not human-reviewed); this round used the fixed six-question subset: A01 exact control, B01 cross-version comparison, C01 official mapping, F01 conflicting mappings, E01 conceptually new control, H02 unsupported question requiring abstention. The other 13 were never run.
- Gold expectations are narrow (e.g. B01 expects only crosswalk row 22), so passing them does not show an answer is complete or correct.

## 3. Six-question results (baseline)
| Q | Category | Answer | [M] deterministic | [J] GPT-OSS (faith / rel / correct / compl / cite, 1–5) | [AI] source review | Human |
|---|---|---|---|---|---|---|
| A01 | exact control | answered | all applicable pass | 5 / 5 / 5 / 5 / 5 | correct, faithful, complete | PENDING |
| B01 (original) | comparison | answered | **fail**: row 22 not cited | **unavailable** (see 7) | partly incorrect; retrieval + generation failure | PENDING |
| C01 | official mapping | answered | all pass | 5 / 5 / 5 / 5 / **2** (per-citation) | correct, faithful, complete | PENDING |
| F01 | conflict | answered | all pass | 5 / 5 / 5 / 5 / **3** (per-citation) | correct, conflict preserved | PENDING |
| E01 | conceptually new | answered | all pass | 5 / 5 / 5 / 5 / **4** (per-citation) | correct; "no direct equivalent" wording stronger than the workbook | PENDING |
| H02 | abstention | abstained | all pass | not judged by design | correct abstention | PENDING |

No aggregate judge score is reported: only four of six questions have a full judgment, B01 and H02 are missing, and a mean over four easy cases would mislead.

## 4. Deterministic validation [M]
Five of six questions pass every applicable check (schema, citation ids valid and in the supplied bundle, official mapping pairs and rows, framework versions, expected rows, conflict preservation, new-control-without-reference, no uncited claims, abstention). C01, F01 and E01 cite exactly the expected rows (4/5, 25/26, 46); H02 abstains as required. B01 fails `expected_rows_covered`: official category-level row 22 (GV.SC → ID.SC) was never cited because it was never retrieved. These checks establish structure and official-record agreement, **not** semantic faithfulness or completeness.

## 5. Source-based semantic findings [AI]
- **A01, C01, F01, E01:** correct and faithful to the stored records (rows 4/5/25/26/46 verified against the workbook; GV.SC-03 text verified). **E01:** the official workbook (row 46) says GV.OV-01 is *conceptually new in CSF 2.0* with *no CSF 1.1 reference listed*. The answer's "no direct equivalent exists in CSF 1.1" / "does not map to any CSF 1.1 element" is a stronger semantic statement than the workbook itself establishes (the workbook lists no mapping; it does not say that no related 1.1 content exists). [AI] preliminary; developer to decide. F01 mentions "pipeline findings", an internal term.
- **H02:** abstention was appropriate for the evidence available — a keyword search of the stored corpus finds zero chunks containing "quantum", "cryptograph", "encrypt" or "crypto". Two limitations, not major failures: a zero-match search is not proof that a concept cannot exist anywhere (it shows only that this corpus has none), and the `uncertainties` aside naming PR.DS/PR.PT as possible locations came from the model's background knowledge, not the supplied evidence.
- **B01 original:** states CSF 1.1 supply chain has "two subcategories" (it has five: ID.SC-1…5); claims "GV.SC-01 through GV.SC-10" from seven supplied records; says the crosswalk maps "these new subcategories back to the two CSF 1.1 subcategories". Retrieval failure (row 22, ID.SC-3/4/5 absent) plus generation overreach.
- Full detail and excerpts: `eval/human_review_packet.md`.

## 6. Available GPT-OSS judgments [J]
Run with the existing rubric (version 1), strict schema, one request per question, from saved answers and saved evidence (no regeneration). **All judgments are LLM opinions, not ground truth.**
| Q | Faithfulness (units supported/unsupported/unclear) | Citation verdicts | Tokens (prompt+output) | Judge latency |
|---|---|---|---|---|
| A01 (earlier run, reused) | 5 (all units supported) | 1 supports | 1,759 + 877 = 2,636 | — |
| C01 | 5 (5/0/0) | 2 supports, 3 does_not_support | 4,291 + 1,802 = 6,093 | 4.2 s |
| E01 | 5 (4/0/0) | 1 supports, 1 does_not_support | 3,940 + 1,413 = 5,353 | 3.4 s |
| F01 | 5 (7/0/0) | 2 supports, 2 does_not_support | 4,611 + 1,887 = 6,498 | 4.3 s |
Estimated request sizes (6.3k / 5.8k / 7.1k tokens, calibrated) were under the 7,500 safety cap for Groq's 8,000 tokens/minute limit; all three requests returned HTTP 200 on the first attempt. Artifact: `eval/live_runs/2026-10-22_judge_C01_E01_F01.json`.

## 7. Missing or failed judgments
- **B01 (original):** the single-call judgment failed twice with Groq HTTP 400 `json_validate_failed` (the second time with strict structured output). Its cause is not proven; a ~14.9k-token estimate for one request against an 8,000 tokens/minute limit suggests a cut-off. Segmented judging was built and **one** batch (S1–S4) succeeded; the remaining 5 requests were deliberately not run. **B01's full judgment is unavailable.** Records preserved in `eval/live_runs/`.
- **H02:** an abstention; checked deterministically and by source review instead of the answer-quality rubric.
- Nothing was judged for the post-hoc B01 repairs.

## 8. Preliminary comparison: judge [J] vs source review [AI]
**Two different citation questions.** *Claim-level support*: does an authoritative citation support the factual claim? (A mapping claim is supported by its official crosswalk row.)
*Per-citation support*: does EACH attached citation individually support the claim? (A supplementary definition chunk for a mapped control does not, alone, establish the mapping.)
My [AI] reading is claim-level; GPT-OSS's citation-support score appears to apply the stricter per-citation reading. The judge's scores are reported **unchanged** — A01 5/5, C01 2/5, F01 3/5, E01 4/5 — and I do not
declare the judge right or wrong: which reading the rubric intends needs developer confirmation.

| Q | Correctness | Faithfulness | Completeness | Citation support | Notes |
|---|---|---|---|---|---|
| A01 | agree | agree | agree | agree (5/5) | |
| C01 | agree | agree | agree | differ: J 2/5; AI claim-level "supports" | rows 4/5 support the mappings; three supplementary chunks counted as non-supporting by J |
| E01 | agree | agree (AI notes the wording point in section 5; J did not) | agree | differ: J 4/5; AI claim-level "supports" | |
| F01 | agree | agree | agree | differ: J 3/5; AI claim-level "supports" | |
| B01 | not comparable | one partial batch only | — | — | see below |
| H02 | — | — | — | — | not judged by design |

Observations about the judge (not validated, not conclusions):
1. **Possible strict per-citation interpretation** — see above; the disagreement may be a definitional difference rather than an error on either side.
2. **Evidence-only faithfulness cannot detect retrieval-induced errors:** in the one successful B01 batch the judge marked "two subcategories" (S1) and "GV.SC-01 through GV.SC-10" (S3) as *supported* because the evidence it saw matched the items listed. A false completeness claim is invisible to a check that only compares claims with supplied evidence.
3. **Ceiling effect:** all judged dimensions other than citation support are 5, on simple official-record lookups; the judge has not been shown to separate good from bad answers.
4. It restates gold facts when justifying correctness, so it cannot catch errors the gold set does not encode.

The agreement above is between two AI readings. **No human-judge agreement is claimed or computed**; it can only be assessed after the developer's confirmation.

## 9. B01: original baseline, retrieval omission and the two post-hoc repairs
**The six-question baseline is the ORIGINAL B01 answer** (deterministic fail; no full judgment). Both repairs below are separate, post-hoc results made after seeing the failure — repair checks, not benchmark results — and neither replaces the baseline. **No B01 version is described here as fully correct or complete.**

Recorded facts:
1. **Original retrieval omission [M]:** official category-level row 22 (GV.SC → ID.SC) and the CSF 1.1 subcategories ID.SC-3/4/5 never reached the generator (they exist in the database and index; top-5 retrieval ranked the ID.SC category 6th and ID.SC-3 10th, and mappings were attached only to a few retrieved controls).
2. **Incorrect claim [AI]:** the original says CSF 1.1 supply chain risk management has "two subcategories" (ID.SC-1, ID.SC-2); CSF 1.1 has five. It also asserts "GV.SC-01 through GV.SC-10" from seven supplied records.
3. **Repair 1 — category-aware evidence expansion:** for broad comparisons, add the category record and the official rows of the category and its subcategories (both versions). Result: row 22 recovered and cited; all applicable deterministic checks pass [M]; the false "two" claim is gone [AI].
4. **Repair 2 — improved evidence selection and a strict 12,000-character budget:** canonical definitions are prioritised before subcategory mappings, the budget is enforced once on the final serialized text (11,963 ≤ 12,000; the first repair had been 12,138), official records that do not fit are omitted and listed in `missing_evidence`. All applicable deterministic checks pass [M].
5. **Still wrong or incomplete in the final answer [AI], pending developer review [H]:** it does not explain what ID.SC-3, ID.SC-4 and ID.SC-5 cover although their definitions were supplied and cited; it calls GV.SC-06, -03 and -10 "new concepts"/"introduces" while mapping them to ID.SC-1/ID.SC-2, which may overstate the novelty of CSF 2.0 concepts; it omits mapping rows 24, 31, 32 and the rows mapping other categories into ID.SC (they did not fit the context; the answer says so).
Comparison: `eval/b01_before_after.md`.

## 10. Known system limitations
- Retrieval depends on top-k similarity; broad comparisons are only repaired by the category expansion and the 12,000-character context can omit official records (reported, not silently).
- Generation sometimes overreaches ("only", "new concept", "no direct equivalent") or ignores supplied definitions; structural citation validation does not prove semantic support.
- An abstention rests on this corpus having no relevant content; a zero-match keyword search is not proof that a concept cannot exist anywhere, and the H02 abstention contained an out-of-evidence aside.
- "Citation support" is ambiguous (claim-level vs per-citation); the judge's scores are not comparable to a claim-level reading until the intended definition is confirmed.
- Qwen was called even for H02 to produce the abstention (no pre-LLM refusal for off-topic questions with retrieved noise).
- Generator and judge share Groq; the judge's evidence-only faithfulness has the blind spot above; judge scores are uncalibrated.
- Gold labels and questions are AI-curated, narrow, and unreviewed; sample of six.
- Free-tier limits (8,000 tokens/minute for the models used) constrain long-answer judging.

## 11. Engineering lessons learned
- Provider reliability dominated schedule: six Gemini 503s, a timeout that crashed the runner (fixed), Mistral 429, and Groq 400s. Budgeting requests, stopping at the first provider error, and recording failures made this cheap to diagnose.
- Measure before assuming: the B01 failure was a retrieval/evidence-assembly issue, found by tracing the actual records, not a model issue; token estimates from chars/3 are conservative (~25%) and the per-minute limit is the binding constraint.
- Narrow gold expectations (one row for B01) pass while answers are still wrong; deterministic checks need human reading beside them.
- Evaluation infrastructure grew faster than the evidence it produces; stop when further engineering no longer changes what a human must review.
- Pin behavior in tests, but expect to rewrite a pinned test when the contract legitimately changes (budget strictness); keep one source of truth for the context budget.

## 12. Outstanding human confirmations
Use `eval/human_verification_checklist.md`. In short:
1. Review each of the six answers in `eval/human_review_packet.md` and sign off correctness, faithfulness, completeness, citation support and relevance (all PENDING).
2. Decide the intended meaning of "citation support": claim-level (an official row supports a mapping claim) or per-citation (every attached citation must support it) — before using the judge's citation scores.
3. Decide whether E01's "no direct equivalent exists in CSF 1.1" (stronger than the workbook's "conceptually new, no 1.1 reference") and H02's out-of-evidence aside are acceptable.
4. Confirm the B01 repair assessment (ID.SC-3/4/5 not explained; "new concepts" framing).
5. Review the gold labels and expected facts themselves (AI-curated, unreviewed).
6. Only after 1–5: compute any judge/human agreement. None is claimed here.

*Artifacts:* `eval/human_verification_checklist.md` (to complete), `eval/live_answer_review.md` (deterministic report), `eval/human_review_packet.md`, `eval/b01_before_after.md`, `eval/live_runs/*` (raw records; originals untouched), `eval/failed_runs/*`.
