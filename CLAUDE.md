# ControlShift

Version-aware RAG over NIST CSF 1.1 vs 2.0. Python 3.11+, src layout (`src/controlshift`).

## Commands
- Activate: `source venv/bin/activate`
- Tests: `pytest`
- Ingest: `controlshift-ingest` (reads data/raw, writes data/processed)
- API: `controlshift-serve` (needs data/processed/controlshift.db and data/indexes; GEMINI_* optional)
- Lint: `ruff check .`

## Rules
- Work in this directory; never create a nested ControlShift folder.
- Build one phase at a time per PROGRESS.md; update it when a phase completes.
- Never fabricate benchmark numbers; report only results from runnable scripts in `eval/`.
- Every chunk carries metadata: framework version, source file, page/sheet, control ID.
- Answers must cite retrieved evidence; refuse when evidence is missing.
- Keep modules small and testable; no model downloads in tests (use fakes/fixtures).
- Raw data, indexes, SQLite files and `.env` are gitignored.
