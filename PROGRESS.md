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

### Phase 4B — Grounded generation + FastAPI  ✅ (live provider NOT tested: no API key was available)
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
- No live Gemini call was made (no GEMINI_API_KEY/GEMINI_MODEL in this environment); `tests/test_live_provider.py` is opt-in via
  `RUN_LIVE_LLM_TESTS=1` and was skipped. Prompt quality and Gemini's JSON compliance are therefore unverified.
- Validation is structural plus rule checks; it cannot detect a fluent but unfaithful paraphrase of a correctly cited chunk.
- The removal-claim guard is a keyword heuristic (can reject benign wording, can miss synonyms).
- Request timeouts return 504 but the worker thread keeps running until the provider timeout fires.
- Context budget is in characters, not tokens; mandatory records may exceed it (reported as `mandatory_over_budget`).
- Single process, no auth, rate limiting or caching; dense/rerank calls are serialised.

## Phase 5 — Evaluation
- [ ] Hand-labeled question set in `eval/`
- [ ] Reproducible scripts: dense vs BM25 vs hybrid vs hybrid+rerank (recall@k, MRR, nDCG)
- [ ] Citation-faithfulness checks; results written only from real runs

## Phase 6 — API & UI
- [ ] FastAPI endpoints (search, compare, mapping lookup)
- [ ] Streamlit UI in `ui/`

## Phase 7 — Hardening
- [ ] CI-style test run, lint, README with real benchmark results, reproducibility notes
