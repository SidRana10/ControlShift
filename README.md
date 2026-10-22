# ControlShift — Version-Aware Enterprise RAG

Analyzes differences between NIST Cybersecurity Framework 1.1 and 2.0 using hybrid
retrieval (dense + BM25 + RRF + cross-encoder reranking), a SQLite-backed control
mapping between versions, and evidence-grounded answers with verifiable citations.

**Status:** Phases 1-5A complete (ingestion, SQLite store, hybrid retrieval + reranking, evidence bundles, grounded generation, FastAPI, retrieval benchmark). See [PROGRESS.md](PROGRESS.md).

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"        # full deps (downloads torch; large)
pip install -e ".[dev,ui]"     # plus Streamlit
cp .env.example .env
pytest
```

## Ingestion

Place the three NIST files in `data/raw/` (`nist_csf_1_1.pdf`, `nist_csf_2_0.pdf`,
`nist_csf_transition.xlsx`), then:

```bash
controlshift-ingest            # writes data/processed/{chunks.jsonl,crosswalk.jsonl,manifest.json}
```

Phase 1 needs only `pymupdf`, `pandas`, `openpyxl` (plus `pytest`, `ruff` for dev).

## Knowledge store

```bash
controlshift-db build      # data/processed/*.jsonl -> data/processed/controlshift.db
controlshift-db validate   # integrity + counts vs ingestion manifest
controlshift-db inspect
controlshift-db map GV.OC-01 --version 2.0     # forward (2.0 -> 1.1) official rows
controlshift-db map ID.BE-2 --version 1.1      # reverse lookup over the same rows
controlshift-db unmapped [--direction no-later|flagged-new] [--level subcategory]
```

## Retrieval

```bash
controlshift-retrieve build-index                  # downloads all-MiniLM-L6-v2 on first run
controlshift-retrieve search "GV.SC-03" --mode bm25
controlshift-retrieve search "protect data at rest" --mode dense --version 1.1
controlshift-retrieve search "manage supplier risk" --mode hybrid_rerank --debug   # bm25|dense|hybrid|hybrid_rerank
```

On macOS, dense search uses an exact NumPy product over the FAISS-stored vectors (faiss-cpu and torch ship
conflicting OpenMP runtimes); see `src/controlshift/retrieval/dense.py` and `--dense-backend`.

## Evidence bundles (no LLM)

```bash
controlshift-evidence "How does GV.SC-03 map to CSF 1.1?"            # JSON: records, official mappings, passages, citations
controlshift-evidence "What changed for supply chain risk management?" --retrieval bm25
```

## Grounded answers and API (Phase 4B)

```bash
cp .env.example .env              # add GEMINI_API_KEY and GEMINI_MODEL to enable generation
controlshift-serve                # or: uvicorn controlshift.api.app:app_factory --factory
curl -s localhost:8000/health
curl -s localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "How does GV.SC-03 map to CSF 1.1?"}'
curl -s localhost:8000/compare -H 'content-type: application/json' \
  -d '{"question": "supplier risk", "control_ids": ["GV.OC-01"]}'
```

**Live Gemini generation has NOT been tested** (no API key was available during development); all generation tests use a fake
provider and mocked HTTP. Without Gemini credentials the API still works and returns `status: "evidence_only"` with the full evidence bundle. Answers are
validated (cited ids must exist in the supplied evidence, mappings must match official crosswalk rows) but citation checks are
structural: they do not prove the answer is faithful to the cited text, and no model confidence is reported.
A live-provider smoke test is opt-in: `RUN_LIVE_LLM_TESTS=1 GEMINI_API_KEY=... GEMINI_MODEL=... pytest tests/test_live_provider.py`.

## Evaluation

```bash
python eval/build_questions.py     # validates the curated labels against SQLite, writes eval/questions.jsonl + audit sheet
python eval/benchmark.py           # runs the 4 retrieval modes with the real models; writes eval/results.json + eval/report.md
```

See `eval/report.md` for measured results and limitations. The relevance labels are AI-curated and source-checked, **not
human-reviewed**; review them in `eval/questions_audit.md`.

## Layout

- `src/controlshift/` — package
- `tests/` — pytest suite
- `data/raw/` — source PDFs/Excel (gitignored)
- `eval/` — retrieval benchmarks
- `ui/` — Streamlit app
