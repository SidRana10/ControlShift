# ControlShift — Version-Aware Enterprise RAG

Analyzes differences between NIST Cybersecurity Framework 1.1 and 2.0 using hybrid
retrieval (dense + BM25 + RRF + cross-encoder reranking), a SQLite-backed control
mapping between versions, and evidence-grounded answers with verifiable citations.

**Status:** Phases 1-2 complete (ingestion, SQLite store). Retrieval and answering are not built yet. See [PROGRESS.md](PROGRESS.md).

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

## Layout

- `src/controlshift/` — package
- `tests/` — pytest suite
- `data/raw/` — source PDFs/Excel (gitignored)
- `eval/` — retrieval benchmarks
- `ui/` — Streamlit app
