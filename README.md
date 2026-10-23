# ControlShift — Version-Aware Enterprise RAG

Analyzes differences between NIST Cybersecurity Framework 1.1 and 2.0 using hybrid
retrieval (dense + BM25 + RRF + cross-encoder reranking), a SQLite-backed control
mapping between versions, and evidence-grounded answers with verifiable citations.

**Status:** the backend (ingestion, SQLite store, hybrid retrieval + reranking, evidence bundles, grounded generation, FastAPI, retrieval benchmark) and the web application (Overview, Ask ControlShift, Control Explorer, Compare Frameworks, in `frontend/`) are implemented. ControlShift has not been deployed; see *Deployment readiness* below and [PROGRESS.md](PROGRESS.md).

## What the application does

- **Ask ControlShift** - questions answered from retrieved NIST evidence with checked citations (needs an LLM provider; without one it shows the evidence only).
- **Control Explorer** - official CSF 1.1 / 2.0 records, provenance and the crosswalk rows for each record. No LLM.
- **Compare Frameworks** - the official transition workbook rows (`GET /crosswalk`), searchable, side by side. No LLM.
- Official NIST text, ControlShift-derived labels and AI-generated text are always labelled differently.

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
cp .env.example .env              # set LLM_PROVIDER (gemini|mistral) and that provider's API key and model to enable generation
controlshift-serve                # or: uvicorn controlshift.api.app:app_factory --factory
curl -s localhost:8000/health
curl -s localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "How does GV.SC-03 map to CSF 1.1?"}'
curl -s localhost:8000/compare -H 'content-type: application/json' \
  -d '{"question": "supplier risk", "control_ids": ["GV.OC-01"]}'
```

**Live status.** A six-question exploratory live evaluation was run with Groq `qwen/qwen3.8-27b` as generator (Gemini returned repeated HTTP 503s and Mistral a 429; both remain
selectable). That is a small exploratory sample, **not an accuracy evaluation**, and ControlShift is not production-deployed. Without LLM credentials the API still works and returns
`status: "evidence_only"` with the full evidence bundle. Answers are validated (cited ids must exist in the supplied evidence, mappings must match official crosswalk rows), but citation checks are
structural: they do not prove the answer is faithful to the cited text, and no model confidence is reported.
The generator is chosen by `LLM_PROVIDER` (`gemini` is the default; `mistral` and `groq` — e.g. Qwen on Groq — are alternatives). The judge is configured separately (`JUDGE_PROVIDER`/`JUDGE_MODEL`, currently Groq `openai/gpt-oss-120b`) and never falls back to the generator.
A live-provider smoke test is opt-in: `RUN_LIVE_LLM_TESTS=1 GEMINI_API_KEY=... GEMINI_MODEL=... pytest tests/test_live_provider.py`.

## Evaluation

```bash
python eval/build_questions.py     # validates the curated labels against SQLite, writes eval/questions.jsonl + audit sheet
python eval/benchmark.py           # runs the 4 retrieval modes with the real models; writes eval/results.json + eval/report.md
```

```bash
python eval/build_answer_questions.py   # gold file for grounded-answer evaluation, verified against SQLite
python eval/answer_eval.py              # OFFLINE: evidence-stage checks + validator self-test; no LLM calls
```

`eval/answer_report.md` and `eval/answer_review_worksheet.md` separate structural checks, deterministic factual checks and
semantic faithfulness; the last is **pending human review** (nothing is scored yet). A live-Gemini mode exists but is disabled by
default (`--live` plus `RUN_LIVE_LLM_EVAL=1`) and has not been run.

```bash
python eval/judge_eval.py          # DRY RUN, 0 API calls: plan, calibration worksheet, report (generator/judge sections say "Not run")
```

An LLM-as-a-judge framework (faithfulness at claim level, relevance, factual correctness, completeness, citation support; plus an opt-in segmented mode for long answers) exists. In the six-question
exploratory run GPT-OSS judged four answers (A01, C01, E01, F01); the original B01 is unjudged and H02 is an abstention. Judge scores are opinions, not ground truth; generator and judge share Groq
infrastructure; and **the judge has not been validated against human reviewers** (no independent human review was completed). Live commands are in `PROGRESS.md`.

**Evaluation status.** Retrieval benchmark: `eval/report.md` (39 AI-labelled questions; chunk ranking only). Six-question live-answer evaluation, complete with documented limitations:
`eval/final_evaluation_report.md` (supporting: `eval/human_review_packet.md`, `eval/b01_before_after.md`, `eval/live_answer_review.md`; raw records in `eval/live_runs/` and `eval/failed_runs/`). Five of six original
answers passed every applicable deterministic check; the original B01 did not (a retrieval omission and a factual error), and its two post-hoc repairs are documented separately.

See `eval/report.md` for retrieval results and limitations. The relevance labels are AI-curated and source-checked, **not
human-reviewed**; review them in `eval/questions_audit.md`.

## Deployment readiness

ControlShift is two processes: the FastAPI backend (Python >= 3.11) and the Next.js frontend (Node >= 20.9; developed on Node 26). The browser only talks to the frontend; the frontend server proxies a fixed set of paths to the backend.

**Build from a clean checkout**

```bash
# backend
python3.12 -m venv venv && source venv/bin/activate && pip install -e .
# the three NIST files are NOT in the repository: place them in data/raw/ first (see Ingestion)
controlshift-ingest && controlshift-db build && controlshift-db validate
controlshift-retrieve build-index      # not needed for RETRIEVAL_MODE=none; downloads all-MiniLM-L6-v2 on first run
# frontend
cd frontend && npm ci && npm run build
```

`data/raw`, `data/processed`, `data/indexes`, `.env` and every `*.db` are git-ignored, so a deployment must produce (or mount) `data/processed/controlshift.db` and, for retrieval modes other than `none`, `data/indexes/` (about 2.5 MB together).

**Run**

```bash
# backend (reads .env; API_HOST defaults to 127.0.0.1, API_PORT to 8000)
controlshift-serve
# frontend (from frontend/)
CONTROLSHIFT_API_URL=http://127.0.0.1:8000 npm run start      # port 3000; PORT=... to change
```

**Configuration**

| Variable | Where | Meaning |
|---|---|---|
| `CONTROLSHIFT_API_URL` | frontend server | Backend base URL. Read at request time (not at build), never sent to the browser. Default `http://127.0.0.1:8000`. |
| `SQLITE_PATH`, `INDEX_DIR` | backend | Relative paths resolve against the backend's working directory: start it from the repository root or set absolute paths. |
| `RETRIEVAL_MODE` | backend | `none` (structured records only), `bm25` (index only, no model), `dense`, `hybrid` (default), `hybrid_rerank`. Dense and hybrid modes load sentence-transformers models at start-up, so the model cache must be available (first run downloads from Hugging Face). |
| `LLM_PROVIDER`, `<PROVIDER>_API_KEY`, `<PROVIDER>_MODEL` | backend | Optional. Without a configured provider `/ask` returns `evidence_only`. Keys live only in the backend environment (`.env` or the host's secret store); the frontend never receives them. |
| `API_HOST`, `API_PORT`, `LLM_TIMEOUT_SECONDS`, `REQUEST_TIMEOUT_SECONDS` | backend | Bind address (use `0.0.0.0` only behind a private network or proxy) and time limits (the frontend waits up to 100s for `/ask`). |

**Health and troubleshooting**

- `GET /health` on the backend (also `/api/backend/health` through the frontend) returns database counts, retrieval mode and `llm.configured`; the sidebar status reads it.
- Sidebar shows "API unreachable": check `CONTROLSHIFT_API_URL` and that `controlshift-serve` is running; the proxy answers 502 when it cannot reach the backend.
- Backend exits at start-up: a missing database ("run `controlshift-db build`"), a stale or missing index (`controlshift-retrieve build-index`), or a model that cannot be downloaded (use `RETRIEVAL_MODE=bm25` or `none`).
- Ask says "No language model is configured": expected without provider credentials.

**Constraints and concerns before a public deployment**

- **No authentication or rate limiting.** Anyone who can reach the frontend can call `POST /api/backend/ask`, which spends LLM provider credit when a provider is configured. Put the app behind access control or a rate limit first, and keep the backend (which also serves `/docs` and the LLM-backed `POST /compare`) on a private network; the frontend proxy forwards only `/ask` and the read-only catalog, crosswalk and health GETs.
- The backend loads its models and runs retrieval in one process (retrieval is serialised by a lock); run a single worker.
- NIST source files must be obtained separately; they are not distributed with the repository.
- Generation quality has only been explored on six questions (see the evaluation notes above); the UI never reports model confidence.
- `npm audit` shows development-only advisories (see `frontend/README.md`); `npm audit --omit=dev` is clean.

## Layout

- `src/controlshift/` — package
- `tests/` — pytest suite
- `data/raw/` — source PDFs/Excel (gitignored)
- `eval/` — retrieval benchmarks
- `ui/` — Streamlit app (legacy prototype; the web application is `frontend/`)
- `frontend/` — Next.js web application (see `frontend/README.md`)
