# ControlShift — Version-Aware Enterprise RAG

Analyzes differences between NIST Cybersecurity Framework 1.1 and 2.0 using hybrid
retrieval (dense + BM25 + RRF + cross-encoder reranking), a SQLite-backed control
mapping between versions, and evidence-grounded answers with verifiable citations.

**Status:** Phases 1-3B complete (ingestion, SQLite store, BM25/dense/hybrid retrieval with reranking). Retrieval and answering are not built yet. See [PROGRESS.md](PROGRESS.md).

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

## Layout

- `src/controlshift/` — package
- `tests/` — pytest suite
- `data/raw/` — source PDFs/Excel (gitignored)
- `eval/` — retrieval benchmarks
- `ui/` — Streamlit app
