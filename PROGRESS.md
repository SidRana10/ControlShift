# Progress

## Phase 0 — Project setup  ✅
Scaffold, pyproject, docs, importable package, smoke test.

## Phase 1 — Data acquisition & ingestion
- [ ] Obtain official NIST CSF 1.1 and 2.0 PDFs and the CSF 1.1→2.0 mapping Excel into `data/raw/`
- [ ] PyMuPDF PDF parser; pandas/openpyxl Excel parser
- [ ] Chunking with metadata (version, source, page/sheet, function/category/subcategory ID)
- [ ] Tests on small fixtures

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
