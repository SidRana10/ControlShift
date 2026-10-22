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
- [ ] Dense index (SentenceTransformers + FAISS) with version filtering
- [ ] BM25 index
- [ ] Reciprocal Rank Fusion
- [ ] Cross-encoder reranker
- [ ] Unit tests with fake embedders

## Phase 4 — Grounded comparison
- [ ] Query routing (single-version vs cross-version)
- [ ] Combine SQLite mappings with retrieved evidence
- [ ] LLM answer generation with citations; citation verification; refusal when unsupported

## Phase 5 — Evaluation
- [ ] Hand-labeled question set in `eval/`
- [ ] Reproducible scripts: dense vs BM25 vs hybrid vs hybrid+rerank (recall@k, MRR, nDCG)
- [ ] Citation-faithfulness checks; results written only from real runs

## Phase 6 — API & UI
- [ ] FastAPI endpoints (search, compare, mapping lookup)
- [ ] Streamlit UI in `ui/`

## Phase 7 — Hardening
- [ ] CI-style test run, lint, README with real benchmark results, reproducibility notes
