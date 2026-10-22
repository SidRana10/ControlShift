# ControlShift — Version-Aware Enterprise RAG

Analyzes differences between NIST Cybersecurity Framework 1.1 and 2.0 using hybrid
retrieval (dense + BM25 + RRF + cross-encoder reranking), a SQLite-backed control
mapping between versions, and evidence-grounded answers with verifiable citations.

**Status:** Phase 0 (scaffold only). No RAG pipeline yet. See [PROGRESS.md](PROGRESS.md).

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"        # full deps (downloads torch; large)
pip install -e ".[dev,ui]"     # plus Streamlit
cp .env.example .env
pytest
```

## Layout

- `src/controlshift/` — package
- `tests/` — pytest suite
- `data/raw/` — source PDFs/Excel (gitignored)
- `eval/` — retrieval benchmarks
- `ui/` — Streamlit app
