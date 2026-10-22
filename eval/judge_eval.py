"""Judged answer-quality evaluation (generator + deterministic checks + LLM judge + human calibration).

DEFAULT (no API calls of any kind):
    python eval/judge_eval.py
  validates configuration, writes the request plan, the calibration worksheet and a report whose
  generator / judge sections say "not run". Existing human calibration input is preserved.

LIVE (explicit opt-in; real, billable requests):
    RUN_LIVE_LLM_EVAL=1 python eval/judge_eval.py --live --subset six \
        --max-generation-requests 6 --max-judge-requests 6
  needs GEMINI_API_KEY + GEMINI_MODEL (generator) and JUDGE_MODEL (+ JUDGE_PROVIDER, JUDGE_API_KEY, which
  defaults to GEMINI_API_KEY for provider gemini). There is NO automatic retry, the run stops at the
  first provider error, and the judge never silently reuses the generator's model: to use the same model
  you must pass --judge-same-as-generator, and the result is then labelled as self-evaluation.
  --subset all runs the 19 valid gold questions (the blank-input question is rejected by the API with 422).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

from controlshift.evaluation.answers import (
    GoldError,
    load_gold,
    validate_gold_against_db,
    validate_gold_schema,
)
from controlshift.evaluation.judge import (
    JudgeSettings,
    judge_human_agreement,
    judge_provider,
    load_calibration,
)
from controlshift.evaluation.judge_report import render_judge_report, render_judge_worksheet
from controlshift.evaluation.judge_run import plan, run_judged_evaluation, select_questions
from controlshift.evidence.assemble import EvidenceAssembler
from controlshift.generation.config import Settings
from controlshift.generation.provider import provider_from_settings
from controlshift.store.queries import KnowledgeStore
from controlshift.store.schema import connect


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--index-dir", type=Path, default=Path("data/indexes"))
    ap.add_argument("--gold", type=Path, default=Path("eval/answer_questions.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=Path("eval"))
    ap.add_argument("--subset", choices=["six", "all"], default="six")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-generation-requests", type=int, default=6)
    ap.add_argument("--max-judge-requests", type=int, default=6)
    ap.add_argument("--retrieval", choices=["bm25", "hybrid", "hybrid_rerank"], default="hybrid")
    ap.add_argument("--judge-same-as-generator", action="store_true",
                    help="use the generator's model as judge (self-evaluation; labelled as not independent)")
    args = ap.parse_args()

    try:
        gold = load_gold(args.gold)
    except GoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors := validate_gold_schema(gold) + validate_gold_against_db(gold, args.db):
        print("gold dataset invalid:\n" + "\n".join(errors), file=sys.stderr)
        return 2
    questions = select_questions(gold, args.subset)
    calib_path = args.out_dir / "judge_calibration.json"
    calibration = load_calibration(calib_path, [g["question_id"] for g in select_questions(gold, "all")])
    if not calib_path.is_file():
        calib_path.write_text(json.dumps(calibration, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_plan = plan(questions)
    live = None

    if args.live:
        if os.environ.get("RUN_LIVE_LLM_EVAL") != "1":
            print("refusing: live mode needs RUN_LIVE_LLM_EVAL=1", file=sys.stderr)
            return 2
        from dotenv import load_dotenv

        from controlshift.evidence.cli import build_retriever
        load_dotenv()
        settings = Settings.from_env()
        gen = provider_from_settings(settings)
        if gen is None:
            print("refusing: generator not configured (GEMINI_API_KEY / GEMINI_MODEL)", file=sys.stderr)
            return 2
        jset = JudgeSettings.from_env()
        if args.judge_same_as_generator:
            jset = dataclasses.replace(jset, provider="gemini", model=gen.model, api_key=settings.gemini_api_key)
        judge = judge_provider(jset)
        if judge is None:
            print("refusing: judge not configured. Set JUDGE_MODEL (and JUDGE_PROVIDER/JUDGE_API_KEY if needed), "
                  "or pass --judge-same-as-generator to accept a non-independent self-evaluation.", file=sys.stderr)
            return 2
        settings = dataclasses.replace(settings, max_llm_attempts=1)
        if args.max_generation_requests > run_plan["max_generation_requests"] or \
                args.max_judge_requests > run_plan["max_judge_requests"]:
            print(f"note: this subset needs at most {run_plan['max_generation_requests']} generation and "
                  f"{run_plan['max_judge_requests']} judge requests", file=sys.stderr)
        retriever, label = build_retriever(args.retrieval, args.db, args.index_dir)
        with KnowledgeStore(args.db) as store:
            live = run_judged_evaluation(
                questions, EvidenceAssembler(store, retriever, label), store, gen, judge, settings, jset,
                min(args.max_generation_requests, run_plan["max_generation_requests"]),
                min(args.max_judge_requests, run_plan["max_judge_requests"]))
        live["subset"] = args.subset
        (args.out_dir / "judge_results_live.json").write_text(
            json.dumps(live, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        b = live["budgets"]
        print(f"live run {live['status']}: generation requests {b['generation_requests_made']}, "
              f"judge requests {b['judge_requests_made']}; independence: {live['independence_note']}")
    else:
        live = _load(args.out_dir / "judge_results_live.json")  # reuse a previous real run, if any

    plan_doc = {"mode": "live" if args.live else "dry_run_no_api_calls", **run_plan, "subset": args.subset,
                "automatic_retries": False, "requests_made_by_this_invocation": 0 if not args.live else
                (live["budgets"]["generation_requests_made"] + live["budgets"]["judge_requests_made"])}
    (args.out_dir / "judge_plan.json").write_text(json.dumps(plan_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    calib_rows = {q: v for q, v in calibration.items()}
    agreement = judge_human_agreement(live["per_question"], calib_rows) if live and live.get("judge_kind") == "live_llm_judge" else None
    report = render_judge_report(_load(args.out_dir / "results.json"), _load(args.out_dir / "answer_results.json"),
                                 live, calibration, agreement)
    (args.out_dir / "judge_report.md").write_text(report, encoding="utf-8")
    conn = connect(args.db, readonly=True)
    (args.out_dir / "judge_review_worksheet.md").write_text(
        render_judge_worksheet(questions, live, calibration, conn), encoding="utf-8")
    print(f"plan: {run_plan['max_generation_requests']} generation + {run_plan['max_judge_requests']} judge requests max "
          f"for subset '{args.subset}' ({'LIVE' if args.live else 'dry run, 0 API calls'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
