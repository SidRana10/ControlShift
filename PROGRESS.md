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

## Phase 2 — Structured store
- [ ] SQLite schema: controls per version, v1.1↔v2.0 mappings (added/removed/moved/reworded)
- [ ] Loader from the NIST mapping spreadsheet; query helpers; tests

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
