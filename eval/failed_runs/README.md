# Failed live attempts (records only)

Sanitized records of real provider failures, kept for honesty about what was tried. They are **not** results:
nothing in `src/` or `eval/*.py` reads this directory, and no report, aggregate or benchmark uses them.

| File | What happened |
|---|---|
| `2026-10-22_gemini_503_six_question_attempt.json` | Six-question run; the first Gemini request (A01) returned HTTP 503 UNAVAILABLE; the run stopped, 1 request made. |
| `2026-10-22_mistral_429_ask_smoke.json` | One Mistral `/ask` smoke test; Mistral returned HTTP 429 rate_limited; no answer. |
| `2026-10-22_gemini_503_ask_a01_smoke.json` | One Gemini `/ask` smoke test on A01 (90 s timeout verified applied, 1 attempt); Gemini returned HTTP 503 UNAVAILABLE after 0.8 s; no answer. |
| `2026-10-22_gemini_503_ask_a01_retry2.json` | Second Gemini `/ask` A01 attempt (90 s timeout verified applied); HTTP 503 UNAVAILABLE after 0.5 s; no answer. |

A third attempt (Gemini read timeout on A01 after 30 s) crashed the runner before it could save anything; the crash was fixed
(`ProviderError` is now recorded like any provider failure) and no record of that attempt exists.

Live runs write `eval/judge_results_live.json` (the runtime artifact, overwritten by each live run). Committed fixtures are the gold
files, `results.json`, `answer_results.json` and the reports; do not move a failed run's output over them.
