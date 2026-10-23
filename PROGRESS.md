# Progress

## Phase 0 — Project setup  ✅
Scaffold, pyproject, docs, importable package, smoke test.

## Phase 1 — Data acquisition & ingestion  ✅
Inputs (in `data/raw/`, gitignored): `nist_csf_1_1.pdf` (55 pp), `nist_csf_2_0.pdf` (32 pp),
`nist_csf_transition.xlsx` (sheet `Relationships`; focal = CSF 2.0, reference = CSF 1.1).

- [x] PyMuPDF extraction with header/footer removal, bold-heading detection (`ingest/pdf.py`)
- [x] Core parsers: 2.0 Appendix A bullet list; 1.1 Table 2 column parser incl. informative
      references, incl. rows that continue across pages (`ingest/controls.py`)
- [x] Section-aware narrative chunking, <=1500 chars, section path + page + printed page
      (`ingest/narrative.py`)
- [x] Stable chunk IDs: `csf{ver}:{function|category|subcategory}:{ID}` and
      `csf{ver}:text:{sha1-12}` (`ingest/models.py`)
- [x] Excel crosswalk parser keeping every original row (`excel_row`, descriptions, comments)
      plus `mapping_type` (`mapped` / `new_in_2_0`) and zero-padded normalized IDs (`ingest/crosswalk.py`)
- [x] Outputs in `data/processed/` (gitignored): `chunks.jsonl`, `crosswalk.jsonl`, `manifest.json`
      (input SHA-256s, counts, validation warnings); byte-identical across runs
- [x] CLI: `controlshift-ingest [--raw-dir] [--out-dir] [--strict]` (or `python -m controlshift.ingest.cli`)
- [x] Tests: 25 passing (real documents + synthetic/invalid inputs); ruff clean

Actual results (384 chunks, no validation warnings):

| | function | category | subcategory | narrative text |
|---|---|---|---|---|
| CSF 1.1 | 5 | 23 | 108 | 71 |
| CSF 2.0 | 6 | 22 | 106 | 43 |

Crosswalk: 205 rows = 185 mapped + 20 "Conceptually new in 2.0" (no reference element);
by focal level: 6 function, 26 category, 173 subcategory. All crosswalk IDs resolve to
controls extracted from the PDFs.

Known limitations / notes:
- Narrative chunks exclude the Core pages (controls are chunked separately); 1.1 Table 1/Table 2
  intro text on Core pages is therefore not in narrative chunks.
- 1.1 Functions have no description in the table, so their chunk text is just the name and ID.
- Unnumbered headings (e.g. "Executive Summary", "Preface") are not detected; that text lands
  in `(front matter)` or the preceding numbered section.
- 2.0 Informative References / Implementation Examples are not in the PDF (online only), so 2.0
  controls have no references.
- Virtualenv is `venv/` (not `.venv/`): in this Documents folder every dot-prefixed directory and
  its contents get the macOS `hidden` flag, and Python 3.12's `site.py` ignores hidden `.pth` files,
  so an editable install inside `.venv/` is silently not importable outside pytest. A non-dot venv
  avoids it with no workaround.

## Phase 2 — Structured store  ✅
`data/processed/controlshift.db` (gitignored), built only from `chunks.jsonl`, `crosswalk.jsonl`,
`manifest.json` (PDFs are never reparsed). Code: `src/controlshift/store/`.

- [x] Schema (`schema.py`): `source_document`, `framework_version`, `element` (function/category/
      subcategory, PK `(version, element_id)`, self-FK to parent), `informative_reference`, `chunk`,
      `chunk_mention`, `crosswalk_mapping`, `build_info`
- [x] Version safety: composite FKs everywhere; `chunk (version, source_file)` must match
      `framework_version`; crosswalk `focal_version` is CHECKed to 2.0 and `reference_version` to 1.1;
      `mapping_type='mapped'` iff a reference exists; foreign keys on for every connection
- [x] Transactional, idempotent loader (`loader.py`): drop + recreate + insert in one transaction;
      any failure rolls back and leaves the previous database intact; rebuilt dump is byte-identical
- [x] Queries (`queries.py`): get control, list category, forward 2.0->1.1 mappings, reverse 1.1->2.0
      (derived from stored official rows), evidence, controls without earlier mapping, controls
      without later mapping, controls flagged new
- [x] Validation (`validate.py`): integrity_check, foreign_key_check, counts vs Phase 1 manifest,
      no invented mappings, hierarchy consistency
- [x] CLI `controlshift-db {build,inspect,validate,get,map,evidence,category,unmapped}`
- [x] Tests: 44 total passing (19 new: real data + synthetic constraint/rollback tests); ruff clean

Loaded counts (match the Phase 1 manifest; `validate` reports no problems):

| table | rows |
|---|---|
| source_document / framework_version | 3 / 2 |
| element | 270 (2.0: 6 fn, 22 cat, 106 sub; 1.1: 5 fn, 23 cat, 108 sub) |
| informative_reference | 504 (1.1 only) |
| chunk | 384 (1.1: 207, 2.0: 177) |
| chunk_mention | 10 |
| crosswalk_mapping | 205 (185 mapped, 20 new_in_2_0) |

Notes:
- Control IDs are keyed zero-padded (`PR.AT-01`) with the printed spelling kept in `original_id`
  (`PR.AT-1`); queries accept either. The same ID can exist in both versions (e.g. `PR.AT-01`).
- Official-data quirk, kept as-is: `GV.SC-03` has both a mapped row (-> ID.SC-2) and a
  "Conceptually new" row. So 20 elements are flagged new but only 19 have no earlier mapping;
  both queries are provided.
- `chunk_mention` only records exact control-ID mentions that resolve to a real control of that
  version; unresolved IDs in prose are dropped.
- Evidence = the control's own chunk plus narrative chunks mentioning its ID; semantic retrieval
  is Phase 3.

## Phase 3 — Retrieval
### Phase 3A — BM25 + dense retrieval  ✅ (independent retrievers; no fusion/reranking yet)
Code: `src/controlshift/retrieval/` (`corpus`, `tokenize`, `bm25`, `dense`, `persist`, `hits`, `cli`).
CLI: `controlshift-retrieve build-index [--mode bm25|dense|all] [--force]` and
`controlshift-retrieve search "<q>" --mode bm25|dense [--version 1.1|2.0] [-k N] [--json]`.

- [x] Corpus read from SQLite only; control chunks are indexed with ID, level, function and category
      titles (e.g. "GV.SC-03 subcategory (Govern / Cybersecurity Supply Chain Risk Management): ...");
      narrative chunks are prefixed with their section path. Displayed text stays the original chunk text.
- [x] BM25 (`rank-bm25` BM25Okapi); tokenizer keeps control IDs as single normalised tokens
      (`PR.AT-1` == `pr.at-01` -> `pr.at-01`, plus category token `pr.at`), light plural folding, stop-words
- [x] Dense: `sentence-transformers/all-MiniLM-L6-v2` (384-d, L2-normalised) in FAISS `IndexFlatIP`
- [x] Version filter before ranking: BM25 builds statistics over only the allowed version; FAISS uses an
      `IDSelectorBatch` inside the search
- [x] Hits carry chunk_id, version, control_id, chunk_type, source_file, page, printed_page, section, text, score, rank
- [x] Persistence in gitignored `data/indexes/` (`docs.jsonl`, `bm25/`, `dense/`); manifest written last
- [x] Cache key = sha256(corpus content hash, preprocessing settings incl. stop-words/tokenizer version,
      embedding model id, format version); `build-index` reuses fresh indexes, `search` refuses stale ones
- [x] Tests: 70 passing in total (26 new, using a deterministic fake embedder - no model download in tests); ruff clean

Actual results:
- Indexed 384 documents (1.1: 207, 2.0: 177) in both indexes.
- Model downloaded on first dense build: `sentence-transformers/all-MiniLM-L6-v2` (87 MB in the HF cache); dense build took ~28 s on CPU.
- Index size on disk: 1,220,451 bytes total (docs.jsonl 428 KB, bm25 192 KB, dense 584 KB).
- Spot checks on real data (top-5 listed in the 3A report): exact ID `GV.SC-03` is rank 1 for BM25 but only
  rank 3 for dense; `PR.AT-1` with `--version 1.1` is rank 1 for BM25; "data at rest" question with
  `--version 1.1` finds `PR.DS-1` at rank 1 for both. No benchmark/recall numbers yet (Phase 5).

Limitations / notes:
- Dense is weak on bare identifiers (hence hybrid retrieval in 3B); BM25 is weak on paraphrase
  (a supplier-risk question ranks GV.RM-05 / ID.SC-5 first, dense ranks GV.SC-07 first).
- all-MiniLM-L6-v2 truncates input at 256 word-pieces: 45 of 384 indexed texts (max 446 tokens) are cut,
  so the tail of long narrative chunks is not embedded. BM25 sees the full text.
- Without `--version`, `PR.AT-1` also matches 2.0's `PR.AT-01` (same normalised ID, by design); use the filter to separate them.
- No stemming beyond plural folding; no query expansion; BM25 drops zero-score hits, dense always returns k.
- Query-time dense search loads the model each CLI call (~seconds); the HF Hub prints an unauthenticated-request warning.
### Phase 3B — Hybrid retrieval + cross-encoder reranking  ✅
New modules: `fusion.py` (RRF), `reranker.py`, `hybrid.py`, `chunking.py`; `dense.py`, `corpus.py`, `persist.py`,
`hits.py`, `cli.py` extended. CLI modes now: `bm25`, `dense`, `hybrid`, `hybrid_rerank`
(`--rrf-k 60 --pool 30 --rerank-pool 30 --reranker-model ... --debug`).

- [x] RRF: score = sum 1/(k+rank) over lists, default k=60; fuses ranks only (raw scores ignored); dedupes by chunk_id
      keeping metadata; tie-break = score, then best rank in any list, then chunk_id (deterministic)
- [x] Candidate pool: top 30 from each of BM25 and dense (configurable), version filter applied inside both retrievers
- [x] Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (downloaded on first `hybrid_rerank` run), scores the fused
      top-30 `(query, index_text)` pairs, max_length 512; model cached per process; optional (`hybrid` skips it)
- [x] Debug info: every hit keeps `components` = per-stage {rank, score} (bm25, dense, rrf/hybrid, rerank)
- [x] Long chunks: 45 of 384 index texts exceeded MiniLM's 256-token limit (max 446). Dense now embeds sentence-window
      passages (<=256 tokens, 1-sentence overlap, context prefix repeated, every sentence covered) and returns one hit per
      parent chunk (best passage wins; `matched_passage` shows which). Real index: 384 docs -> 430 passages.
      BM25, the SQLite DB and ingestion are untouched; citations still point at the parent chunk/page/section.
- [x] FAISS filtering: version filter is an `IDSelectorBatch` inside the search; the search widens until k distinct parent
      docs are found. Verified equal to exhaustive search within the version: 15 fake-embedder cases in tests, and 0
      mismatches in 18 real-model cases (6 queries x {all, 1.1, 2.0}, k=10)
- [x] Cache key now also covers dense chunking settings (max tokens, overlap, strategy) and format version 2
- [x] Tests: 111 passing (41 new). Mocked embedder/scorer unit tests plus `tests/test_integration_real_models.py`, which
      runs the real MiniLM + cross-encoder through the CLI in subprocesses (auto-skipped if the models are not cached)
- Index on disk after rebuild: 1,505,225 bytes (docs.jsonl 456 KB, bm25 192 KB, dense 836 KB)

Real-run observations (single queries, NOT a benchmark - no claim that hybrid is better; that needs Phase 5):
- `GV.SC-03`: bm25 #1 = GV.SC-03; dense #3; hybrid puts GV.SC-02 first because RRF ties GV.SC-02 (bm25 #3, dense #1) with
  GV.SC-03 (bm25 #1, dense #3) and the tie-break falls to chunk_id; hybrid_rerank puts GV.SC-03 #1.
- "How should organizations manage supplier risks?": rankings differ a lot by mode (bm25 favours narrative text; dense favours
  GV.SC-07/06/04; rerank favours 1.1 ID.SC category). Relevance of these is unjudged.
- "How should sensitive information be protected at rest?": PR.DS-1 / PR.DS-01 near the top in all modes; without a
  version filter, 1.1 and 2.0 results are interleaved.

Known limitations:
- Equal-weight RRF can tie on exact-ID queries (above); weights/ID-aware boosting were not added.
- The cross-encoder is a general web-search model (MS MARCO): it cannot read control IDs, and scores are unbounded logits
  (negative values are normal). It also truncates at 512 tokens (longest index text is 446).
- The reranker only sees the fused pool (<=60 unique candidates, 30 by default); anything outside it cannot be recovered.
- Each CLI call reloads the models (several seconds); there is no long-running service yet.
- Passage overlap is one sentence; sentence splitting is regex-based.

### Phase 3B reliability fix — macOS FAISS + torch OpenMP abort  ✅
- Root cause (reproduced in fresh subprocesses): the macOS wheels of `faiss-cpu` and `torch` each bundle their own
  `libomp.dylib` (`faiss/.dylibs/` and `torch/lib/`). LLVM's OpenMP runtime aborts with `OMP: Error #15` once both copies
  are exercised in one process. Experiments: a FAISS search plus a torch import/op aborts in either order; `import faiss`,
  `IndexFlat.add`, `write_index/read_index` and `reconstruct_n` do NOT trigger it; `OMP_NUM_THREADS=1`, `torch.set_num_threads(1)`
  and `faiss.omp_set_num_threads(1)` do NOT help; only `KMP_DUPLICATE_LIB_OK=TRUE` (documented by Intel/LLVM as unsafe) bypasses it.
  Whether it fires depends on which ops run, so the earlier "works if torch is loaded first" was luck, not a guarantee.
- Fix (no package changes, no env hacks): FAISS still builds, saves and loads the index, but search runs as an exact NumPy
  matrix product over the stored vectors (`DenseIndex(backend=...)`, `--dense-backend auto|numpy|faiss`,
  `CONTROLSHIFT_DENSE_BACKEND`). `auto` = numpy on macOS, faiss elsewhere. Results are identical (flat exact index; tested
  for both backends incl. version filters); on-disk index format and cache keys are unchanged. Details: `retrieval/dense.py`.
- Regression tests (`tests/test_openmp_regression.py`, fresh subprocesses): canary that still reproduces the abort (skips if
  new wheels fix it), thread-limiting is not a fix, supported sequence (3 rounds of torch work / FAISS build+write+read /
  numpy search) exits 0, forced `faiss` backend + torch still aborts. The test process never imports torch itself.
- Real-model checks: `tests/test_integration_real_models.py` runs encode/search/rerank interleaved in ONE process (6 queries x
  {all,1.1,2.0} x {hybrid,hybrid_rerank} x 2 rounds + 64-text batch encodes) and all four CLI modes; both pass.
  A forced-`faiss` run of the same real-model sequence happened not to abort, so the real-model path is only conditionally
  affected; the synthetic canary shows the failure is real.
- Reranker truncation: `CrossEncoderScorer` counts tokens and, if (query + passage) would exceed 512, scores sentence windows
  and takes the max instead of truncating (unit-tested). Over the real corpus 0 passages needed windowing (longest index
  text 446 tokens), asserted in the real-model test. Reranker input is the context-enriched `index_text`, not a snippet.
- Tests now: 137 passing (26 new in this fix), ruff clean. RRF weights and ID boosting unchanged (left for Phase 5).
- Safety: on macOS an explicit `--dense-backend faiss` (or `CONTROLSHIFT_DENSE_BACKEND=faiss`) now exits 2 with an actionable
  message before any model loads; `CONTROLSHIFT_ALLOW_UNSAFE_FAISS=1` overrides it for diagnostics only (used by the tests).
- Remaining limitation: the FAISS search backend is unusable with torch on macOS. Linux/Windows wheels were not
  tested, so `auto` keeps FAISS there.

## Phase 4 — Grounded comparison
### Phase 4A — Query planning, evidence assembly, structural citation checks  ✅ (no LLM)
Code: `src/controlshift/evidence/` (`planner`, `assemble`, `bundle`, `citations`, `cli`).
CLI: `controlshift-evidence "<question>" [--retrieval none|bm25|dense|hybrid|hybrid_rerank] [-k 5] [--compact]` prints the
evidence bundle as JSON (default retrieval = hybrid; `none` = structured records only; no API keys, no network).

Planner (rule-based, deterministic; `plan_query`):
- Extracts explicit versions (`CSF 1.1`, `version 2.0`, `v2.0`; "section 1.1"/"page 2.0" are ignored) and control IDs
  (any case, normalised like the store: `pr.at-1` -> `PR.AT-01`; function/category/subcategory). ID-like strings with an
  unknown function code (e.g. `ZZ.AB-01`) are reported, never guessed.
- Types: `control_mapping` (control ID + mapping/comparison cue, or both versions named), `single_version` (incl. exact control
  lookup), `cross_version_comparison` (comparison/mapping/"new" cue or both versions, no IDs), `unsupported` (empty question).
- Uncertainty is carried into `unresolved_questions`: no version named (both searched separately), comparison with one named
  version (baseline unstated), relative wording ("previous", "latest"), removal wording (the crosswalk has no "removed" status),
  an ID present in both versions with no version named.

Evidence assembly (`EvidenceAssembler`):
- Exact control records come from SQLite, not similarity. In mapping questions a named version may be source or target, so
  controls are looked up in all versions; single-version lookups honour the named version (no silent substitution: a control missing
  from the named version is `missing_evidence`, with a note if it exists in the other version).
- Official mappings only from stored crosswalk rows: forward (2.0->1.1) and reverse (1.1->2.0), counterpart controls attached as
  records. Conceptually-new elements -> `unmapped_controls` with the official reason; a 1.1 control no row points to -> reported as
  "no crosswalk row" (explicitly not "removed"); an element with both a mapped and a new row (GV.SC-03) -> `conflicts`
  (`mapped_and_new_in_2_0`), both rows kept, neither preferred.
- Passages: retrieval runs per version (k=5; k=3 for mapping questions) so comparisons always carry both versions; for comparisons
  the top retrieved controls also pull their official crosswalk rows; "new"-type questions add all 20 official `new_in_2_0` rows.
- Bundle fields: question, query_type, plan, referenced/searched versions, control_ids, control_records, crosswalk_records,
  passages, citations (registry), conflicts, unmapped_controls, missing_evidence, unresolved_questions, retrieval info.
  Citation IDs: `chunk:<chunk_id>` and `xwalk:row<excel_row>`.

Citation validation (`validate_citations`, `validate_bundle`) is STRUCTURAL only: the cited chunk/crosswalk row exists; stated
version, source file, page, section, control and mapping endpoints equal the database; (optionally) the citation belongs to the bundle;
bundle text equals stored chunk text. Whether an answer's claims are supported by the cited text (semantic faithfulness) is not
checked and is reported as out of scope in every validation result.

Real runs (hybrid_rerank over the real corpus; all citations valid):
- "How does GV.SC-03 map to CSF 1.1?" -> control_mapping; records GV.SC-03 (2.0 p.22) and ID.SC-2 (1.1 p.35); rows 25 (mapped to
  ID.SC-2) and 26 (new_in_2_0); one `mapped_and_new_in_2_0` conflict; 9 citations, 0 invalid.
- "What are the differences between CSF 1.1 and 2.0 for supply chain risk management?" -> cross_version_comparison; 5 passages per
  version, 14 control records, official rows for the retrieved controls; 32 citations, 0 invalid.
- "How should sensitive information be protected at rest in CSF 1.1?" -> single_version, searched ['1.1'] only; PR.DS-1 first;
  5 citations, 0 invalid.

Tests: 217 passing (78 in the evidence suites, incl. routing regressions for the cases above; planner routing/extraction/uncertainty; single-version and version isolation; exact lookup; both-version
IDs; one-to-many and many-to-one mappings; reverse lookups; new/unmapped; the GV.SC-03 conflict; 1.1 element with no row; unknown
and unsupported questions; missing evidence; positive and negative citation validation incl. tampered bundles; CLI). Ruff clean.

Known limitations:
- Routing is rule-based. Incidental words ("new technologies", "changes in the threat landscape", "between") no longer trigger a
  comparison: only strong cues (compare, differences, versus, ...), both versions named, or a change idiom ("what is new", "what
  changed", "added in 2.0", "changed from") anchored to a named version or control ID do. An unanchored idiom ("What changed?") stays
  single-version, searches both versions and records the ambiguity. Idioms outside the listed patterns are missed (-> single-version).
- Only function/category/subcategory IDs are detected; function names in prose ("the Govern function") are not.
- A version number typed without "CSF"/"version"/"v" is accepted unless preceded by section/page/figure/table/appendix.
- Counterpart controls are fetched for explicitly named IDs and for the top 3 retrieved controls per version only.
- Passage relevance is whatever the retriever returns (not yet benchmarked); structural validity does not imply faithful answers.
- 1.1 vs 2.0 same-ID pairs (e.g. PR.AT-1 / PR.AT-01) are different statements; both are reported when the version is not named.

### Phase 4B — Grounded generation + FastAPI  ✅ (built with a fake provider; see Phase 5B step 1 for the later live check)
Code: `src/controlshift/generation/` (`config`, `provider`, `schema`, `context`, `prompt`, `generate`) and `src/controlshift/api/`
(`app`, `schemas`, `services`). Dependencies added to the core set: `httpx` (Gemini REST + TestClient); no vendor SDK.

- Provider: `LLMProvider` protocol; `GeminiProvider` calls `generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent`
  with the key in the `x-goog-api-key` header. Key and model come only from `GEMINI_API_KEY` / `GEMINI_MODEL` (no defaults in code);
  timeout `LLM_TIMEOUT_SECONDS` (30). Without both set, `provider_from_settings` returns None, no HTTP client is created, and the
  pipeline runs evidence-only. Errors map to `ProviderNotConfigured` / `ProviderTimeout` / `ProviderFailure` with messages that never
  contain the key, URL or response body.
- Context (`build_context`, budget `GENERATION_CONTEXT_CHARS`=12000): exact control records and official crosswalk rows are always
  included (descriptions trimmed first if they alone exceed the budget); passages fill the rest, interleaved across versions so
  comparisons keep both; identical text within one version is merged but the merged citation ids stay citable; omitted/truncated items
  are reported. All evidence is HTML-escaped inside `<evidence id=... version=... page=... section=...>` blocks, treated as untrusted
  data in the system prompt, and passages resembling instructions are flagged in `warnings`.
- Output contract (Pydantic `LLMAnswer`): answer, key_changes[{statement,citations}], citations, mappings[{focal_id,reference_id,note,
  citations}], uncertainties, unresolved_questions, abstained, abstention_reason. Unknown keys such as a self-reported `confidence` are dropped.
- Deterministic validation before anything is returned: JSON/schema valid (one repair retry, `LLM_MAX_ATTEMPTS`); every cited id is in the
  supplied context and passes the Phase 4A structural validators; non-abstaining answers need top-level citations and a citation on every
  key change/mapping; every mapping must equal a cited official crosswalk row (focal=2.0 id, reference=1.1 id or null for `new_in_2_0`);
  "removed/deleted/retired/dropped..." statements are rejected unless a cited item says so. Failures give `status: "rejected"` and withhold
  the answer text. Crosswalk conflicts (GV.SC-03) are always surfaced via `system_uncertainties` if the model did not mention them.
- Abstention: no evidence or an unsupported question abstains without calling the LLM; the model may also abstain explicitly.
- Statuses: `answered`, `abstained`, `evidence_only` (no provider or `generate:false`), `rejected`. Every response carries a disclaimer that
  validation is structural, semantic faithfulness is not verified, and no confidence is reported.
- API: `GET /health`; `POST /ask {question, version?, retrieval_k, generate, include_evidence}`; `POST /compare {question, control_ids?}`
  (prefixes "Compare CSF 1.1 and CSF 2.0 ..."). Models/indexes are loaded once in the app lifespan (`build_services`, including a warm-up
  call); dense search keeps the NumPy backend on macOS; retrieval calls are serialised with a lock, DB connections are per request.
  Errors use `{"error": {code, message, details}}`: 422 invalid_request, 502 provider_error, 504 provider_timeout / request_timeout
  (`REQUEST_TIMEOUT_SECONDS`), 500 internal_error (no internals leaked).
- Tests: 280 passed + 1 skipped = 281 collected (217 from Phase 4A + 64 new: 25 API, 38 generation, 1 opt-in live test; none removed): provider/HTTP mocks, flow, invalid output, fabricated/out-of-bundle citations, invented and
  uncited mappings, removal claims, conflicts, abstention, version isolation, budget/dedupe, prompt injection with a poisoned DB copy,
  API validation/errors/timeouts, service reuse). Ruff clean.
- Real (non-LLM) smoke run: app with RETRIEVAL_MODE=hybrid_rerank started in 3.8 s (embedder + cross-encoder loaded once); /health ok;
  /ask and /compare returned `evidence_only` with valid evidence (`/compare` for GV.OC-01 returned official rows 4 and 5); blank question -> 422.

Not tested / limitations:
- At the end of Phase 4B no live Gemini call had been made (superseded by Phase 5B step 1 below); `tests/test_live_provider.py`
  stays opt-in via `RUN_LIVE_LLM_TESTS=1` and is skipped in normal runs.
- Validation is structural plus rule checks; it cannot detect a fluent but unfaithful paraphrase of a correctly cited chunk.
- The removal-claim guard is a keyword heuristic (can reject benign wording, can miss synonyms).
- Request timeouts return 504 but the worker thread keeps running until the provider timeout fires.
- Context budget is in characters, not tokens; mandatory records may exceed it (reported as `mandatory_over_budget`).
- Single process, no auth, rate limiting or caching; dense/rerank calls are serialised.

## Phase 5 — Evaluation
### Phase 5A — Retrieval benchmark  ✅ (answer-faithfulness evaluation still open)
Code: `src/controlshift/evaluation/` (`metrics`, `dataset`, `runner`, `report`); scripts `eval/build_questions.py`,
`eval/benchmark.py`; artifacts `eval/questions.jsonl`, `eval/questions_audit.md`, `eval/results.json`, `eval/report.md`.
Re-run: `python eval/build_questions.py && python eval/benchmark.py` (`--render-only` rebuilds report.md from results.json).

- Dataset: 40 questions (39 final, 1 provisional): exact_id 11, semantic 10, version_specific 11, cross_version 8; easy 14 /
  medium 19 / hard 7; 21 with a version filter, 19 unfiltered; 73 labelled chunks (59 grade-2, 14 grade-1).
- Label provenance: written by Claude from the stored source text and the official crosswalk rows; no retrieval output was used. Each
  label carries chunk id, version, control id, file, page, section, a source excerpt and a "why". `build_questions.py` fails on a
  nonexistent chunk; tests re-verify every label against SQLite (including that cited crosswalk rows involve the labelled control).
  **Not human-reviewed** (`human_reviewed: false` everywhere); audit via `eval/questions_audit.md`. Uncertain query S08 is
  `provisional` and excluded from headline metrics.
- Metrics: Recall@1/5/10, MRR@10, nDCG@5 (graded, 2^g-1), Hit@5, version-isolation accuracy; overall, per category, per mode; seeded
  bootstrap 95% CIs and paired differences vs BM25; repeated chunk IDs counted once; dense passages scored as parent chunks.
- Fairness: same questions/filters/corpus/top-10, one process, models loaded once, NumPy dense backend, default pool 30 / RRF k 60 /
  rerank pool 30; nothing was tuned on these questions.

Measured results (39 final queries, Apple M4, embedder and cross-encoder ran on MPS):

| Mode | R@1 | R@5 | R@10 | MRR@10 | nDCG@5 | Hit@5 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| BM25 | 0.530 | 0.791 | 0.893 | 0.836 | 0.780 | 0.897 | 0.2 | 0.4 |
| Dense | 0.278 | 0.714 | 0.816 | 0.606 | 0.594 | 0.846 | 5.5 | 6.7 |
| Hybrid RRF | 0.479 | 0.821 | 0.859 | 0.790 | 0.771 | 0.897 | 5.8 | 7.3 |
| Hybrid + cross-encoder | 0.585 | 0.876 | 0.902 | 0.905 | 0.848 | 0.974 | 113.4 | 172.3 |

- Version isolation: 1.000 for every mode (21 filtered queries).
- Paired nDCG@5 vs BM25: dense -0.187 (CI excludes 0); hybrid -0.009 [-0.080, +0.055]; hybrid+rerank +0.067 [-0.006, +0.155]
  (CI includes 0). So only "dense < BM25" is statistically distinguishable at n=39; hybrid ~ BM25 on this set.
- Hybrid vs the better of its two parts (nDCG@5): better on 7 queries, worse on 11. Reranker vs plain hybrid: better on 13, worse on 5
  (S09, V04, V06, X02, X04). Exact-ID queries: hybrid+rerank nDCG@5 0.993, BM25 0.857, hybrid 0.903, dense 0.599.
- Cold start (once per process): MiniLM load + first encode 6.0 s, cross-encoder 0.4 s, FAISS index 0.04 s.
- Tests: 315 passed + 1 skipped (35 new: metrics, dataset/label integrity, aggregation, latency helpers, report generation, BM25
  reproducibility and report/results sync); ruff clean.

Limitations: small n and wide CIs; AI-written, unreviewed labels; unlabelled-but-relevant chunks count as misses; questions mostly
paraphrase control text (favours lexical overlap); tiny structured corpus; latency from one machine/device (MPS) and not a load test;
no tuning or ID boosting was tried (must be evaluated on a separate held-out set to avoid overfitting to these questions).

### Phase 5B, step 1 — Live Gemini verification  (partially complete)
Model: `gemini-3.6-flash` (from `GEMINI_MODEL`; credentials live only in the gitignored `.env`, never printed or committed).
- Direct provider test (1 real request, `max_llm_attempts=1`): question "How does GV.SC-03 map to CSF 1.1?" with the real hybrid
  retrieval pipeline. HTTP 200, `finishReason: STOP`, response keys `candidates/usageMetadata/modelVersion/responseId`, parts carry
  `text` (+ `thoughtSignature`), which the provider's parser handles. Usage: 3115 prompt + 629 output + 1155 thinking tokens.
  Result `status: answered`, schema valid, 4 answer citations structurally valid (GV.SC-03, ID.SC-2, xwalk rows 25 and 26), 0 invalid
  bundle citations. The answer quoted GV.SC-03 and ID.SC-2 text matching the stored source, reported both official mappings
  (row 25 -> ID.SC-2; row 26 "Conceptually new in 2.0" with no reference) and stated that the official records conflict. Semantic
  faithfulness was only eyeballed by the developer for this single answer; it is not verified by the pipeline.
- FastAPI `/ask` with the live provider: NOT verified at that time (verified once later with gemini-3.8-flash; see the sections below). Every attempt after the successful direct call returned Google
  `503 UNAVAILABLE` ("model is currently experiencing high demand"), which the API reported as a controlled `502 provider_error` with no
  leak. The no-LLM path (`generate:false`) and the health endpoint work against the real stack. Retried at spaced intervals, then stopped.
- Evidence levels: (a) LIVE, verified once: direct `GroundedGenerator` + Gemini call. (b) LIVE, NOT verified: FastAPI `/ask` with
  Gemini (only 503s). (c) MOCKED/OFFLINE: all automated tests (316 passed, 1 skipped) use a fake provider or mocked HTTP; the
  skipped live test is opt-in and was not run in the suite.
- Real API requests made in total: 6 (1 success, 5 x 503 which returned no content). No batch evaluation was run.
- Small change: provider errors now include Google's short status token (e.g. "HTTP 503 UNAVAILABLE"); message text is never copied
  (test added). No automatic retry was added; a bounded retry/backoff for 429/503 is a decision for later.
- Limitations: one question, one successful response; Gemini JSON compliance across question types, latency under load and answer
  faithfulness are untested; transient 503s are surfaced to the caller as 502.

### Phase 5B, step 2 — Grounded-answer evaluation framework (offline; NO model calls)
Code: `src/controlshift/evaluation/answers.py`, `answer_report.py`; scripts `eval/build_answer_questions.py`, `eval/answer_eval.py`;
artifacts `eval/answer_questions.jsonl` (gold), `eval/answer_results.json`, `eval/answer_report.md`, `eval/answer_review_worksheet.md`,
`eval/answer_review.json` (reviewer input; all pending). Re-run: `python eval/build_answer_questions.py && python eval/answer_eval.py`.

- Gold: 20 questions - exact_control 3, comparison 3, official_mapping 3, one_to_many 2, conceptually_new 2, conflict 2 (GV.SC-03),
  missing_mapping 1 (RC.CO-2, the only 1.1 subcategory no crosswalk row references), abstention 3 (unknown control GV.XX-99; quantum-safe
  cryptography; penalties for not implementing GV.SC-03), invalid_input 1 (blank question: the API returns HTTP 422 and never reaches
  retrieval or generation - this is NOT an evidence-based abstention). The two topic-absent abstentions are justified by several concept
  terms having zero occurrences (quantum/post-quantum/cryptograph/encrypt/crypto; penalt/sanction/punish/consequence/noncompliance),
  not by one missing keyword, plus a written justification and recorded review of the nearest related passages (e.g. 1.1 'compliance'
  and 'voluntary'), whose counts are re-verified against the corpus. For the penalty question an explicit "the documents define no
  penalty" reply would also be reasonable; the automatic check is deliberately strict (only an explicit abstention passes). Each records expected controls+versions, official crosswalk rows (read from SQLite by control ID), quoted facts,
  conflict/new/unmapped constraints, allowed versions and abstention conditions. Verified against the DB at build time and in tests
  (quotes are substrings of stored chunks, rows involve the stated pairs, "absent" terms occur nowhere in the corpus). Labels are
  AI-curated and **not human-reviewed**; no generated answer was used as ground truth.
- Three assurance levels, kept apart: structural (ids exist / in bundle), deterministic factual (mappings equal official rows, versions,
  conflicts preserved, new controls get no reference, no invented/forbidden mappings, removal wording supported, abstention right,
  expected rows/controls covered, claims cited), and semantic faithfulness (always `requires_human_review`, never decided by code).
- Offline results (all deterministic, reproducible byte-for-byte):
  * Evidence stage - REGRESSION VALIDATION of the deterministic pipeline, not live-model accuracy (BM25 retrieval, no models): 20 of 20
    questions passed every applicable check (including the blank question being rejected by the API request models). The pipeline handed over the expected
    controls and official rows, flagged the GV.SC-03 conflict and unmapped/new controls, reported the unknown control, abstained
    deterministically on the blank question, and kept versions isolated. Caveat: the gold author also built the pipeline, so this is
    a regression check, not proof of robustness; retrieval-dependent comparison questions (B01-B03) passed with BM25 and were not
    tried with other modes.
  * Validator self-test: 19 of 19 gold-derived reference answers accepted (the invalid-input question has none); 15 injected defect types (fabricated/out-of-bundle citation,
    invented or mis-cited mapping, wrong version, unsupported removal claim, dropped conflict row, reference for a new control, mapping
    for an unmapped control, missing row/control, answering instead of abstaining, unwarranted abstention, uncited claim, invalid
    structure) were each detected in every applicable fixture (see `eval/answer_report.md` for counts). This measures the checker on
    synthetic inputs, not any model.
- Human review: `eval/answer_review.json` has 20 entries, all `pending`; groundedness/completeness are unscored. The worksheet shows,
  per question, expected facts, the evidence the pipeline assembled, check results and PENDING review fields. Reviewer input survives
  regeneration; invalid review values are rejected.
- Live mode exists but is disabled: `RUN_LIVE_LLM_EVAL=1 python eval/answer_eval.py --live --live-limit 3` (needs Gemini credentials,
  one attempt per question, writes `answer_results_live.json` with the generated answers and deterministic check results for review).
  It was not run. Results carry `is_live_model`, true only for the real provider, so fake-provider runs in tests are never reported as
  model accuracy.
- Tests: 374 passed + 1 skipped (58 new: gold integrity and corruption, valid/invalid citations, invented/mis-cited mappings, versions,
  conflicts, new/unmapped controls, abstention, missing evidence, invalid structures, review tracking, aggregates, reproducibility,
  live mode disabled by default); ruff clean.

Remaining for Phase 5B: run the live mode on a few questions once Gemini capacity allows (and re-check FastAPI `/ask` live); have a human
review the gold labels and the generated answers; extend to hybrid/rerank evidence and to unseen questions; calibrate the removal-wording
heuristic against real outputs.

### Phase 5B, live FastAPI `/ask` verification with gemini-3.8-flash  (ONE successful smoke test - not an accuracy evaluation)
After `gemini-3.6-flash` kept returning 503 (below), `GEMINI_MODEL` was changed to `gemini-3.8-flash` and one controlled request was made
through the real FastAPI `/ask` endpoint (TestClient, real services, hybrid retrieval, `LLM_MAX_ATTEMPTS=1`, no retries, budget of 1 request).
- Question: "How does GV.SC-03 map to CSF 1.1?" (gold F01, the mapped-and-conceptually-new conflict).
- Requests: exactly 1 real Gemini request; 1 success (HTTP 200 from Gemini and from `/ask`); 0 provider errors; 13.4 s end-to-end latency
  (single observation).
- Outcome: `status: answered`, 1 attempt, no rejection, no warnings. Schema valid. 4 citations, all structurally valid and inside the evidence
  bundle: `chunk:csf2.0:subcategory:GV.SC-03`, `chunk:csf1.1:subcategory:ID.SC-2`, `xwalk:row25`, `xwalk:row26`.
- Official mappings: the answer's two mapping claims matched official crosswalk rows exactly - GV.SC-03 -> ID.SC-2 (row 25) and
  GV.SC-03 -> no CSF 1.1 reference (row 26, "Conceptually new in 2.0"); nothing invented; row coverage complete.
- Conflict handling: the pipeline flagged `mapped_and_new_in_2_0`; the model reported both records, stated that they conflict and chose neither.
- Deterministic answer checks (the Phase 5B step 2 checker): 14 checks, 12 pass, 2 not applicable (`new_control_no_reference`,
  `no_forbidden_mappings`), 0 fail.
- What this does NOT show: one question on one model is a smoke test, not an accuracy measurement. Not tested live: conceptually-new or
  unmapped controls, one-to-many mappings, comparisons, abstention, and other models/prompts. The checks are structural and rule-based;
  whether the prose is faithful and complete is still pending human review (the worksheet stays PENDING), and the quoted definitions were
  only eyeballed.
- Artifact (sanitized: statuses, timings, answer text, check results; no key, headers or raw provider response):
  `eval/live_verification_ask_gv_sc_03.json`.

### Earlier attempt with gemini-3.6-flash (blocked by 503)
- Setup: model `gemini-3.6-flash`, hybrid retrieval, real FastAPI `/ask` via TestClient with the real services, `LLM_MAX_ATTEMPTS=1` (no repair
  retry, no automatic retry anywhere), a hard budget of 3 provider requests and a stop-on-first-error guard. Credentials came from the gitignored
  `.env`; the key never appears in output or artifacts (asserted before writing). Plan: F01 (GV.SC-03 conflict), E01 (conceptually-new GV.OV-01),
  then C01 (official one-to-many mapping) only if the service responded normally.
- Result: 1 real request, 1 failure. Gemini returned HTTP 503 UNAVAILABLE in 0.68 s; `/ask` returned a controlled 502 `provider_error` in 0.71 s.
  F01/E01/C01 were therefore not generated: E01 and C01 were deliberately not attempted. Total real requests in this attempt: 1 (all prior
  attempts: 6 requests, 1 success, 5 x 503; running total 7).
- At that point nothing new was verified live; the gemini-3.8-flash test above later covered `/ask` generation and the GV.SC-03 conflict.
- Sanitized artifact: `eval/live_verification.json` (statuses, timings, error code; no key, no raw provider response).
- Resolution: a later request with `gemini-3.8-flash` succeeded (see above). The 503 was a service-side condition on the earlier model; our code
  handled it as designed and no code change was needed.

### Phase 5B, step 3 — LLM-as-a-judge framework (built and tested OFFLINE; ZERO real API calls made)
Code: `src/controlshift/evaluation/judge.py` (rubric, schema, judging, aggregation, calibration), `judge_run.py` (orchestration),
`judge_report.py` (report + calibration worksheet); script `eval/judge_eval.py`. Artifacts from the default dry run: `eval/judge_plan.json`,
`eval/judge_report.md`, `eval/judge_review_worksheet.md`, `eval/judge_calibration.json` (19 entries, all pending).

- Dimensions judged separately, rubric v1 (documented in `judge_report.md`): **faithfulness** (claim-level: claim, evidence ids, supported /
  unsupported / unclear, justification; the 1-5 value is derived as 1 + 4 x supported-rate, not scored by the judge), **answer relevance**,
  **factual correctness** (against the source-verified gold facts), **completeness**, **citation support** (1-5 plus per-citation verdicts).
  Judge output is schema-validated; a judge cannot cite evidence ids it was not given; invalid output is recorded as missing and not repaired
  (default 1 attempt); provider errors are never retried.
  Methodology audit (claim coverage): the application splits each answer into numbered UNITS (sentences, key changes, mapping claims) and the
  judge must account for every unit - cover it by claims or declare it non-factual (allowed only for plain hedges; units that name controls,
  quote text, or are key changes/mappings cannot be dismissed). A judgment that omits a unit is invalid and counts as a missing judgment, so an
  unsupported claim cannot disappear by being left out. Faithfulness is computed per unit (a unit is supported only if every claim covering it
  is), so adding extra supported claims cannot inflate it. An answer with no factual units, or with no citations for the citation dimension, is
  **not applicable** (None, excluded from means), never an automatic 5. Faithfulness uses ONLY the retrieved evidence; gold facts are used only for
  factual correctness and completeness (stated in the prompt and rubric; claims may cite only supplied evidence ids).
- The judge is NOT ground truth and does not replace the deterministic validators, which remain authoritative for official mappings,
  mapping completeness, versions, conflicts, structural citations, unmapped controls and abstention. Abstentions are not sent to the judge.
- Independence: the judge is configured separately (`JUDGE_PROVIDER`, `JUDGE_MODEL`, `JUDGE_API_KEY`, ...) with NO fallback to the generator's
  model (`--judge-same-as-generator` must be passed explicitly). Every result records the pairing and an independence note: same model =
  self-evaluation; different models of the same provider = independence NOT established; different providers = reduced but not removed
  correlation. Using Gemini to judge Gemini is not an independent evaluation.
- Human calibration: `eval/judge_calibration.json` holds, per question, five 1-5 human scores, reviewer, notes and judge/human disagreement
  notes (all pending). `judge_human_agreement` reports exact agreement, within-one, mean absolute difference, signed bias and a list of 2+ point
  disagreements, only for questions both judged by a real judge run and human-reviewed; with none reviewed the report says no agreement figure exists.
- Subsets: `--subset six` = A01 (exact control), B01 (cross-version comparison), C01 (official mapping), F01 (GV.SC-03 conflict), E01
  (conceptually new), H02 (unsupported question requiring abstention); `--subset all` = the 19 valid gold questions (H04, a blank input rejected
  with HTTP 422, is excluded).
- Safety: hard separate request budgets for generator and judge, no automatic retries, stop at the first provider error, live mode needs `--live`
  plus `RUN_LIVE_LLM_EVAL=1`, and refuses unless generator and judge are configured. Results record `kind` (`real_generator` only for a live
  provider) and `judge_kind`; a mocked run is never reported as generator or judge results.
- Report structure keeps four result types apart: offline fixtures, real generator (deterministic checks, latency), LLM judge, human-reviewed.
  Sections without data say **Not run** and show no numbers. Retrieval effectiveness is pulled unchanged from `eval/results.json`.
- Tests: 439 passed + 1 skipped (65 new, all with mocked judge/generator responses): rubric and prompt (injection escaping), schema and bounds,
  scoring math, id rules, invalid output, no-retry behaviour, independence notes and settings, aggregation with missing judgments, calibration and
  agreement statistics, orchestration (mock labelling, budgets, stop-on-error, missing judge), report/worksheet structure, CLI refusals.

Judge provider support: `JUDGE_PROVIDER` may be `gemini` or `groq`. The Groq adapter (`GroqProvider` in `generation/provider.py`) speaks Groq's
OpenAI-compatible chat-completions API (`https://api.groq.com/openai/v1`, Bearer auth, JSON-object response mode, temperature 0) behind the same
`generate(system, prompt)` interface, with the same controlled errors (timeout, HTTP status plus a short error code token, empty/truncated output)
and no key, URL or message text in error messages. A Groq judge uses `JUDGE_API_KEY` (or `GROQ_API_KEY`) and never receives the Gemini key.
Configured locally: generator `gemini-3.8-flash`, judge `groq` / `openai/gpt-oss-120b` (different providers: correlation reduced, not removed).
Verified offline only (mocked HTTP): request shape, parsing, error mapping, settings, and end-to-end use inside the unchanged judging logic.

Live Groq smoke test (2026-10-22, `eval/groq_judge_smoke.json`): ONE real request to `openai/gpt-oss-120b`, reusing the saved Gemini answer for F01
(GV.SC-03) with its evidence bundle re-assembled offline; 0 Gemini requests, no retries or repair. Result: HTTP 200 (`finish_reason=stop`), latency
5.5 s, 4,260 prompt + 2,251 completion tokens (1,229 reasoning). JSON-object mode returned a valid JSON object that passed the `JudgeOutput`
schema and the id/coverage validation; all 8 answer units (S1-S4, K1-K2, M1-M2) were accounted for with valid evidence references; the judge
scored faithfulness 5/5 (8/8 units supported) and judged all 4 citations as supporting. This is a PROVIDER SMOKE TEST only: one question, one
request, no human review. It is not an accuracy benchmark and does not show the judge is correct or well calibrated (all scores were 5, so
discrimination is untested). Still unverified: behaviour across the six-question set, token/rate limits at scale, and agreement with humans.

Exact commands for a small live run later (a real, billable run; nothing below has been executed):
```bash
# 1. set JUDGE_MODEL in .env (ideally a model from a different provider/family than the generator; see the independence note)
RUN_LIVE_LLM_EVAL=1 python eval/judge_eval.py --live --subset six \
    --max-generation-requests 6 --max-judge-requests 6          # at most 12 requests; writes eval/judge_results_live.json
python eval/judge_eval.py                                        # re-renders report + worksheet from the saved live results (0 API calls)
# all 19 valid questions: --subset all --max-generation-requests 19 --max-judge-requests 19
# same model as judge (self-evaluation, labelled as such): add --judge-same-as-generator
```
After a live run, a human fills `eval/judge_calibration.json` (guided by `eval/judge_review_worksheet.md`) and re-runs the dry-run command to see agreement.

Remaining evaluation limitations: no real judge or human-calibrated result exists yet; unit splitting is rule-based (sentence regex), so exotic
phrasing may merge or split claims oddly; the non-factual check is a heuristic (IDs, quotes, "CSF", citation markers); whether a unit is truly
supported is still the judge's opinion; judge and generator share a vendor unless a different provider is configured; gold facts and retrieval
labels are AI-curated and not human-reviewed; samples of 6 or 19 questions cannot support accuracy claims.
Remaining work: run the live subset; human review of gold labels, answers and judge scores; decide on a judge from a different provider; larger samples.

### Phase 5B, step 4 — Provider stabilization and live-evaluation readiness  (offline; live evaluation NOT yet completed)
- **Configuration:** primary generator Gemini `gemini-3.8-flash` (`LLM_TIMEOUT_SECONDS=90`, `LLM_MAX_ATTEMPTS=1`), judge Groq `openai/gpt-oss-120b`
  (`JUDGE_MAX_ATTEMPTS=1`). `LLM_PROVIDER` selects the generator (`gemini` default | `mistral`); the judge never falls back to it.
- **Mistral (optional backup, `MistralProvider`, `mistral-small-latest`):** OpenAI-style chat completions, JSON mode, controlled errors with no key/URL
  in messages. Verified offline only. ONE live `/ask` attempt returned HTTP 429 `rate_limited` (record in `eval/failed_runs/`); it has never produced
  an answer, so its behaviour with ControlShift's schema is unverified. Not selected.
- **Kept fixes:** provider timeouts are recorded like any provider failure and stop the run (a Gemini read timeout used to crash the runner);
  per-call token usage (`prompt/output/reasoning/total`, counts only) and the model id the API reports (`resolved_models`) are saved per run;
  `evidence_supplied` stores, per question, the exact evidence texts shown to the generator and judge; the report has a token table.
- **Live attempts so far (all failed at the first Gemini request; none produced answers or scores):** HTTP 503 (record kept), a 30 s read timeout
  (crashed the runner before saving anything; fixed), and one Mistral 429. Sanitized records live in `eval/failed_runs/` (see its README); nothing in
  `src/` or `eval/*.py` reads them. The live runner overwrites `eval/judge_results_live.json`, which is the runtime artifact.
- **Still true:** the single Groq judge smoke test (see above) and the single Gemini `/ask` smoke test are the only successful live calls. No
  six-question result, judge calibration or human review exists.

### Phase 5B, step 5 — Groq (Qwen) as an alternative generator  (offline only; ZERO live calls)
- **Why:** `gemini-3.8-flash` returned 503 on every live attempt (6 earlier + the 6-question run + the A01 `/ask` smoke test; records in
  `eval/failed_runs/`) and Mistral returned 429. Gemini and Mistral stay implemented and selectable; nothing was removed.
- **Selection:** `LLM_PROVIDER=groq` uses `GroqProvider.from_settings`: generator model `GROQ_MODEL` (target `qwen/qwen3.8-27b`), key `GROQ_API_KEY`
  (defaults to `JUDGE_API_KEY` when `JUDGE_PROVIDER=groq`, i.e. the same Groq account; Gemini/Mistral keys are never reused). The judge keeps
  `JUDGE_MODEL=openai/gpt-oss-120b`. Both are plain `GroqProvider` instances with separate models, request budgets (`Budgeted`) and recorded
  `resolved_models`. Optional `GROQ_REASONING_FORMAT` is sent only when set; `<think>...</think>` text is stripped from replies regardless. Validation
  of citations, official mappings, conflicts and abstention is unchanged (the output goes through the same `GroundedGenerator`).
- **Independence disclosure:** generator and judge are different model families (Qwen vs OpenAI GPT-OSS) on the SAME Groq infrastructure/account/rate
  limits, so correlated errors are reduced, not removed; the run's `independence_note` says this explicitly. Not independent of the platform.
- **Token-per-minute planning:** one earlier Groq judge call used about 6.5k tokens (4.3k prompt + 2.3k completion incl. reasoning), and a generation
  call adds a similar-sized prompt, so a six-question run could send tens of thousands of tokens in a minute. Groq's actual free-tier limits for these
  models were NOT checked here (look them up in the Groq console). `--pause-seconds N` (default 0) waits between questions without adding requests;
  suggest `--pause-seconds 60`. No automatic retry: a 429 stops the run.
- **Live smoke test PASSED (2026-10-22, `eval/live_verification_groq_qwen_ask_gv_sc_03.json`):** ONE FastAPI `/ask` request ("How does GV.SC-03 map to
  CSF 1.1?") to Groq `qwen/qwen3.8-27b` (reported model id identical), 90 s timeout, 1 attempt, no repair; 0 judge/Gemini/Mistral requests. HTTP 200,
  status `answered`, 1.79 s end to end, 3,141 prompt + 572 output = 3,713 tokens. Schema, citation and all deterministic checks passed: it reported
  GV.SC-03 -> ID.SC-2 (row 25) and the "new in 2.0, no reference" record (row 26), preserved the conflict, invented no mappings. Groq's rate-limit
  headers for this model showed 8,000 tokens/min and 1,000 requests (4,547 tokens left after the call). This is a smoke test of ONE question: it
  does not show semantic faithfulness (not verified) or general accuracy.
- **Still unverified live:** behaviour on the other question types, and the judge's token limit (see above).

### Phase 5B, step 6 — Segmented judging for long answers  (offline-tested; ONE live batch verified)
- **Problem:** in the first six-question run (Qwen generator, GPT-OSS judge) the judge failed on B01 (17 answer units) with Groq HTTP 400 `json_validate_failed`,
  and again in a single-call retry using strict structured output (`eval/live_runs/`). The 400's cause is not proven. A conservative offline estimate
  puts one B01 judge request at ~14.9k tokens (prompt + schema + expected output) against the 8,000 tokens/minute limit Groq reported for the model, which fits an
  output cut-off, but that remains an inference. Rubric, schema and scoring were not changed.
- **Method (`evaluation/judge_segments.py`, opt-in via `--judge-mode segmented|auto`, default `single`):** the deterministic answer units are grouped into
  ordered batches (<=4 units and an estimated <=6,500 tokens); each batch call sees the question, ONLY its units and the relevance-selected subset of
  the evidence the generator was given (never anything else, never the gold facts), and returns claims, non-factual declarations and citation assessments
  (each cited id assessed in exactly one batch). One final holistic call sees the whole answer and gold facts and scores relevance, factual correctness,
  completeness and citation support (not averages of batches; citation support is scored from the batch citation verdicts). Merged output goes through the
  unchanged `validate_judgment` and `derive_scores`. Any failed or rejected call => the judgment is `incomplete` (no scores, nothing imputed); completed
  batches can be reused on a later invocation. Every judgment records `mode` and its limitations. Every segmented request counts against the judge budget
  and is paced like any other request. Limitations: batches see only a subset of the evidence and cannot see each other; segmented and single-call scores
  are not directly comparable.
- **B01 plan:** 5 batches (S1-S4, S5+K1, K2+K3+M1+M2, M3-M6, M7-M9) + 1 holistic call = **6 judge requests** to finish B01.
- **Live check (ONE request):** batch B1 (S1-S4) of the saved B01 answer, strict `judge_batch` schema: HTTP 200 in 4.3 s, valid JSON and schema, all four
  units assessed (all `supported`), both assigned citations `supports`; 3,401 prompt + 1,851 output (1,113 reasoning) = 5,252 tokens (estimate was 6,401).
  Groq reported 4,274 of 8,000 tokens left afterwards, so batches must be spaced (>= ~30 s, the planned 75 s is safe). One batch is NOT a judgment of B01:
  its status is `incomplete`; no scores exist. Record: `eval/live_runs/2026-10-22_B01_segmented_batch_B1_smoke.json`.
- B01's missing official row 22 is a retrieval-stage omission (the row was never in the evidence bundle); the deterministic failure is kept as is.

### Phase 5B, step 7 — B01 retrieval fix: category-aware evidence for broad comparisons  (one live retest; see `eval/b01_before_after.md`)
- **Six-question baseline (2026-10-22, Qwen generator, deterministic checks only for C01/F01/E01/H02):** A01, C01, F01, E01, H02 passed all applicable checks;
  B01 failed `expected_rows_covered` (official row 22 never cited) and said CSF 1.1 had "two subcategories" (ID.SC-1, ID.SC-2); CSF 1.1 ID.SC actually has five. Report:
  `eval/live_answer_review.md` (human review PENDING; no judge used). Baseline artifacts are unchanged.
- **Root cause (verified in the stored records):** ingestion was fine (ID.SC-1..5, both category chunks and row 22 exist in the DB and index). Retrieval takes the top 5 hits
  per version: in 1.1 the ID.SC category chunk ranked 6th and ID.SC-3 10th; in 2.0 all five hits were narrative text (GV.SC category 7th). Official mappings were attached
  only for the top few retrieved *controls*, so row 22 and the ID.SC-3/4/5 rows never entered the bundle. Planning (cross-version comparison) and the context budget were not
  the cause (the budget only dropped narrative passages).
- **Fix (general, no B01 specifics; `evidence/assemble.py`):** for CROSS_VERSION questions only, when >=2 retrieved hits of a version fall in one category, add the category
  record and the official crosswalk rows of the category and all its subcategories, and expand the category the crosswalk pairs with it in the other version. (Superseded by step 8: the
  budget is now enforced once, in the context builder.) One sentence added to the generator
  rules: never call a control list complete/limited ("only", "exactly N") unless a cited block says so. Narrow questions (exact control, mapping) are byte-identical to before
  (test). Existing test `test_cross_version_comparison_gathers_...` was updated (rows may now come via `category_expansion`; row 22 is expected).
- **Retest (ONE Qwen request, 0 judge/Gemini/Mistral; `eval/live_runs/2026-10-22_B01_retest_after_category_expansion.json`):** answered; ALL applicable deterministic checks pass,
  including row 22; the false "two subcategories" claim is gone; 13 official mappings (incl. the GV.SC-03 conflict rows 25/26); tokens 4,223 + 1,984. Remaining gaps: the answer
  does not state "ID.SC-1..5" explicitly nor describe ID.SC-3/4/5, and no longer mentions GV.RM-05 / ID.RA-10. This is a post-hoc repair check on one question, NOT a benchmark;
  human review PENDING. Tests: 507 passed, 2 skipped; ruff clean.

### Phase 5B, step 8 — Definitions-first evidence priority and a strict context budget  (LAST planned backend iteration; one final live B01 retest)
- **Findings:** the first fix carried crosswalk rows but dropped the canonical definitions of ID.SC-3/4/5 and GV.SC-xx, so the corrected B01 answer listed mappings without saying what
  those subcategories cover; its serialized evidence was 12,138 chars vs the 12,000 budget (separators/merge markers were not counted) and a second budget knob existed in the assembler.
- **Changes:** (1) `EvidenceAssembler` no longer knows a budget; category expansion adds every subcategory record plus official rows to the (complete) structured bundle. (2)
  `generation/context.py::build_context` is the single place that enforces `Settings.context_chars` (from `GENERATION_CONTEXT_CHARS`) on the FINAL text: blocks, attributes, merge markers and
  newline separators; official records are never cut, and low-priority ones are omitted deterministically. Priority (selection only; emission order is unchanged): category definitions ->
  subcategory definitions of the compared categories -> category-level mappings -> conflicting rows -> other mappings inside the compared categories -> mappings reaching outside ->
  other control records -> passages. Narrow bundles (no category records) keep controls first and are unchanged. (3) `GroundedGenerator` appends `official_records_omitted_for_context_budget`
  to `missing_evidence` (once) and a warning, so the structured result and the model both see the gap. (4) A previously pinned test ("official records are never displaced even at budget=1")
  was replaced with the strict-budget contract.
- **Tests:** 516 passed, 2 skipped, ruff clean (new: definitions, strict budget at several sizes, priority under shrinking budgets, explicit omissions, configuration propagation, three other
  category pairs, narrow-question serialization, no hardcoding).
- **Final B01 retest (ONE Qwen request; 0 judge/Gemini/Mistral; `eval/live_runs/2026-10-22_B01_final_retest_budget_priority.json`):** answered; all applicable deterministic checks pass; serialized evidence
  11,963 of 12,000 chars; 4,455 + 1,979 = 6,434 tokens; 7.7 s. The answer now enumerates ID.SC-1..5, moves Identify -> Govern with row 22 and preserves the GV.SC-03 conflict, and says records were
  omitted for the budget. **Remaining limitations (documented, not optimised further):** it does not explain what ID.SC-3/4/5 cover even though their definitions were supplied, it omits mapping rows
  24/31/32 and the rows mapping other categories into the compared one (they did not fit), and it frames mapped GV.SC items as "new concepts". Three-way comparison: `eval/b01_before_after.md`
  (post-hoc repair criteria, not a benchmark; human review PENDING). Next phase: Next.js frontend (Phase 6).

### Phase 5 — closure summary  ✅ (exploratory scope; COMPLETE WITH DOCUMENTED LIMITATIONS)
- **Retrieval benchmark (5A):** complete (`eval/report.md`; 39 AI-labelled questions; unchanged).
- **Six-question live-answer evaluation:** complete with Groq `qwen/qwen3.8-27b` (generator) and `openai/gpt-oss-120b` (judge). Report: `eval/final_evaluation_report.md` (supersedes `eval/final_evaluation_draft.md`,
  kept for traceability); supporting: `eval/human_review_packet.md`, `eval/human_verification_checklist.md` (blank, optional), `eval/b01_before_after.md`, `eval/live_answer_review.md`. Raw records: `eval/live_runs/`, failures `eval/failed_runs/`.
- **Deterministic validation:** original A01, C01, F01, E01, H02 pass every applicable check; original B01 fails `expected_rows_covered` (official row 22 never retrieved) and also made an incorrect claim (CSF 1.1 has five ID.SC subcategories, not two).
- **Judge results (GPT-OSS; opinions, unvalidated):** A01, C01, E01, F01 judged (faithfulness/relevance/correctness/completeness 5; citation support 5, 2, 4, 3 for A01, C01, E01, F01). Original B01: unjudged (two failed single-call attempts, one partial segmented batch). H02: abstention, not judged. No aggregate score is reported.
- **B01:** failure investigation (retrieval top-k scattered the category; mappings were attached only to a few retrieved controls) -> category-aware expansion -> definitions-first priority and a strict 12,000-character final-text budget. Both repairs are post-hoc, preserved separately, and pass the deterministic checks; the final answer still does not explain ID.SC-3/4/5 and may overstate novelty.
- **AI-assisted source verification:** the original workbook rows (4, 5, 22, 25, 26, 28, 31, 32, 46) and PDF text were read directly from `data/raw/`. The workbook has **no `mapping_type` column**; `mapped`/`new_in_2_0` are ControlShift-derived labels. A literal search of both PDFs and the workbook found no "quantum"/"cryptograph"/"encrypt"/"crypto" text (H02's abstention was appropriate; this does not prove no related concept exists). F01's rows 25 and 26 are an apparent dual-entry ambiguity, not a proven NIST error.
- **Human verification:** NOT performed. The developer approved closing the phase without a completed checklist; `eval/judge_calibration.json` is all `pending`; no judge/human agreement exists.
- **Known limitations retained:** six questions only (no accuracy claim); AI-curated, unreviewed gold labels (B01 expects only row 22); generator and judge share Groq; judge blind spot for retrieval-induced false completeness; citation-support definition (claim-level vs per-citation precision) unresolved; free-tier 8,000 tokens/minute limits; Gemini 503s; ControlShift is not production-deployed.
- Superseded open items: live `/ask` recheck, answer-faithfulness evaluation (done exploratorily), held-out retrieval question set (still open, not needed for Phase 6).

## Phase 6 — Frontend  (IN PROGRESS: catalog API and app shell done; Control Explorer next)
Approved stack: Next.js, React, TypeScript, Tailwind CSS and selectively customized shadcn/ui, with a same-origin proxy to the FastAPI service (so no CORS middleware). Planned experiences: Control Explorer (first), Compare Frameworks, Ask ControlShift. Authoritative structured data is shown independently of LLM generation.

### Phase 6A - Backend discovery and read-only Catalog API  ✅
- **Discovery audit (read-only, no code changes):** documented the `/health`, `/ask`, `/compare` contracts, the SQLite model and the gaps for a browsing frontend. Findings: no browse/search/detail routes existed; subcategories have no `name` (the description is the title); the five CSF 1.1 functions have no description; the crosswalk covers functions, categories and subcategories (134 distinct CSF 2.0 elements).
- **New read-only endpoints** (`src/controlshift/api/catalog.py`, no LLM, no retrieval, no new data source):
  - `GET /catalog/versions` - version name, source document (file, sha256, bytes, pages) and per-level element counts, derived from the database.
  - `GET /catalog/elements` - typed element summaries; optional `version`, `level`, `function`, `category`, `q` (case-insensitive substring over IDs, names, descriptions; LIKE wildcards escaped); parameterized SQL, ordered by (version, element_id); no pagination (270 elements); invalid filters return the existing 422 envelope.
  - `GET /catalog/elements/{version}/{element_id}` - identity, parent/children, informative references, source-document and page provenance, and every official crosswalk row for the element. Accepts original (`PR.AT-1`) and normalized (`PR.AT-01`) spellings; unknown IDs return the established 404 `not_found` envelope.
- **Reuse:** existing `KnowledgeStore` methods (`get_control`, `get_evidence`, `mappings_2_0_to_1_1`, `mappings_1_1_to_2_0`) plus four small read-only additions (`list_versions`, `list_elements`, `list_children`, `get_source_document`). `/ask`, `/compare`, `/health`, retrieval, generation and evaluation are unchanged.
- **Crosswalk fidelity:** every original workbook row is returned unmerged and individually identifiable (`excel_row`, sheet, source file); direction is stated (CSF 2.0 focal -> CSF 1.1 reference); 2.0 elements use a forward lookup, 1.1 elements a reverse lookup; one-to-many mappings stay as separate rows. `mapping_type` is a ControlShift ingest label, not a workbook column.
- **Derived summary:** each element's `crosswalk.summary` is marked `derived: true` and uses `mapped_only`, `new_in_2_0_only`, `mapped_and_new_in_2_0`, `no_crosswalk_reference` or `unclassified`. Absence of a row is never described as removal.
- **GV.SC-03:** row 25 maps to ID.SC-02 and row 26 has no reference with the comment "Conceptually new in 2.0"; both are returned, with summary `mapped_and_new_in_2_0` (1 mapped, 1 new, rows [25, 26]) and neither preferred.
- **Deferred:** the summary logic in `catalog.py` mirrors the "mapped and new" detection in `evidence/assemble.py` rather than sharing a helper (a shared extraction would touch evidence code); a `/crosswalk` listing route; pagination.
- **Verification:** 24 new tests in `tests/test_catalog_api.py`; full suite 540 passed, 2 skipped; Ruff clean; no external provider calls.

### Phase 6A.3-6A.4 - Frontend design specification  ✅
- `docs/frontend-design-spec.md` is the approved implementation reference (tokens, shell, Explorer, `CrosswalkEntry`, responsive rules, accessibility, states). Implementation adjustments recorded in it: `fg-3` is `#676C75` (4.53-5.28:1 on all surfaces), the sidebar collapse toggle sits at the bottom of the sidebar, and nav labels are 13px.

### Phase 6B.1 - Next.js foundation and application shell  ✅
- **Foundation (`frontend/`):** Next.js 16.4.2 App Router, React 19.3, strict TypeScript, Tailwind CSS 4, ESLint, selectively customized shadcn/ui (Base UI) and Lucide; npm with a committed lockfile; no state, auth, analytics or animation libraries.
- **Design system:** approved tokens as CSS variables mapped to Tailwind (colours, type scale, radii, overlay shadow); IBM Plex Sans, IBM Plex Mono and Source Serif 4 via `next/font` (all three confirmed loading in a browser); focus-visible and reduced-motion handling.
- **Shell:** 232px/56px collapsible sidebar (preference in localStorage, applied before first paint via an inline script so there is no width flash), 56px header, 56px rail at 900-1199px, 52px mobile top bar with an accessible navigation sheet; skip link and landmarks; sidebar status driven by the real `/health` response.
- **Routes:** `/` Overview, `/explorer` (framework summaries from the live API plus loading/error/empty states), `/ask` and `/compare` (honest placeholders, no mock data, no LLM requests), custom not-found page.
- **API integration:** typed client for `/health` and the three Catalog endpoints (backend snake_case, error envelope, unreachable/unexpected handling); same-origin Next.js rewrites under `/api/backend/*` limited to those four read-only GET endpoints (`CONTROLSHIFT_API_URL`, default `http://127.0.0.1:8000`); `/ask` and `/compare` are not proxied; backend unchanged, no CORS.
- **Verification:** ESLint, `next typegen` + `tsc`, and production build pass, including from a clean `npm ci`; browser checks at 1440/1280/1024/390px (no horizontal overflow, no hydration errors, collapse/mobile navigation/focus/404/error states, proxy behaviour); no external LLM calls. No automated frontend tests yet.
- **Known advisory (development-only):** `npm audit` reports 9 high entries from one `braces` advisory (GHSA-vfj7-8cjw-p6xm, no patched release); `npm audit --omit=dev` reports 0. Not remediated; see `frontend/README.md`.

### Phase 6B.2 - Control Explorer navigator  (NEXT)
- [ ] Hierarchical navigator, search and filters, record detail with provenance and `CrosswalkEntry`, per the design spec.
- [ ] Compare Frameworks (needs a crosswalk-listing endpoint) and Ask ControlShift experiences afterwards.

## Phase 7 — Hardening
- [ ] CI-style test run, lint, README with real benchmark results, reproducibility notes
