"""Grounded-answer evaluation runner.

Default (offline, no model calls, no network):
    python eval/answer_eval.py
writes eval/answer_results.json, eval/answer_report.md, eval/answer_review_worksheet.md and
creates eval/answer_review.json (all PENDING) if it does not exist yet. Existing reviewer input is kept.

Optional live mode (DISABLED unless every condition holds):
    RUN_LIVE_LLM_EVAL=1 python eval/answer_eval.py --live --live-limit 3
needs GEMINI_API_KEY / GEMINI_MODEL, makes at most --live-limit generation requests (one attempt each),
and writes eval/answer_results_live.json + a worksheet that contains the generated answers.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

from controlshift.evaluation.answer_report import render_answer_report, render_worksheet
from controlshift.evaluation.answers import (
    GoldError,
    load_gold,
    load_reviews,
    run_evidence_stage,
    run_live,
    validate_gold_against_db,
    validate_gold_schema,
    validator_self_test,
)
from controlshift.evidence.assemble import EvidenceAssembler
from controlshift.generation.config import Settings
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.store.queries import KnowledgeStore
from controlshift.store.schema import connect


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/processed/controlshift.db"))
    ap.add_argument("--index-dir", type=Path, default=Path("data/indexes"))
    ap.add_argument("--gold", type=Path, default=Path("eval/answer_questions.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=Path("eval"))
    ap.add_argument("--live", action="store_true", help="call the real LLM (needs RUN_LIVE_LLM_EVAL=1)")
    ap.add_argument("--live-limit", type=int, default=3)
    ap.add_argument("--retrieval", default="bm25", choices=["bm25", "hybrid", "hybrid_rerank"],
                    help="evidence retrieval for live mode (offline mode always uses bm25)")
    args = ap.parse_args()

    try:
        gold = load_gold(args.gold)
    except GoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors := validate_gold_schema(gold) + validate_gold_against_db(gold, args.db):
        print("gold dataset invalid:\n" + "\n".join(errors), file=sys.stderr)
        return 2

    docs = load_corpus(args.db)
    bm25 = BM25Index.build(docs)
    conn = connect(args.db, readonly=True)
    with KnowledgeStore(args.db) as store:
        assembler = EvidenceAssembler(store, bm25.search, "bm25")
        results = {
            "meta": {"n_questions": len(gold), "retrieval": "bm25",
                     "gold_sha256": hashlib.sha256(args.gold.read_bytes()).hexdigest(),
                     "by_category": dict(sorted(collections.Counter(g["category"] for g in gold).items())),
                     "human_reviewed_labels": False, "mode": "offline"},
            "evidence_stage": run_evidence_stage(gold, assembler, store),
            "validator_self_test": validator_self_test(gold, conn),
            "semantic_faithfulness": "requires_human_review (not evaluated)",
        }
        reviews = load_reviews(args.out_dir / "answer_review.json", [g["question_id"] for g in gold])
        generated = None
        if args.live:
            if os.environ.get("RUN_LIVE_LLM_EVAL") != "1":
                print("refusing: live mode needs RUN_LIVE_LLM_EVAL=1", file=sys.stderr)
                return 2
            from dotenv import load_dotenv

            from controlshift.evidence.cli import build_retriever
            from controlshift.generation.provider import (
                ProviderNotConfigured,
                provider_from_settings,
            )
            load_dotenv()
            settings = dataclasses.replace(Settings.from_env(), max_llm_attempts=1)
            provider = provider_from_settings(settings)
            if provider is None:
                print("refusing: GEMINI_API_KEY / GEMINI_MODEL are not configured", file=sys.stderr)
                return 2
            retriever, label = build_retriever(args.retrieval, args.db, args.index_dir)
            live_assembler = EvidenceAssembler(store, retriever, label)
            try:
                live = run_live(gold, live_assembler, store, provider, settings, args.live_limit)
            except ProviderNotConfigured as exc:
                print(f"refusing: {exc}", file=sys.stderr)
                return 2
            generated = live["per_question"]
            (args.out_dir / "answer_results_live.json").write_text(
                json.dumps(live, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            results["live"] = {k: live[k] for k in ("provider", "model", "is_live_model", "questions_run")}
            print(f"live run: {live['questions_run']} question(s); see answer_results_live.json")

    text = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    (args.out_dir / "answer_results.json").write_text(text, encoding="utf-8")
    review_path = args.out_dir / "answer_review.json"
    if not review_path.is_file():
        review_path.write_text(json.dumps(reviews, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    loaded = json.loads(text)
    (args.out_dir / "answer_report.md").write_text(render_answer_report(loaded, reviews), encoding="utf-8")
    (args.out_dir / "answer_review_worksheet.md").write_text(
        render_worksheet(gold, loaded, reviews, generated), encoding="utf-8")
    a = loaded["evidence_stage"]["aggregate"]
    st = loaded["validator_self_test"]
    print(f"evidence stage: {a['questions_all_checks_passed']}/{a['n_questions']} questions passed all checks; "
          f"failed: {a['failed_questions']}")
    print(f"validator self-test: {st['fixtures_accepted']}/{st['fixtures_built']} fixtures accepted; "
          + ", ".join(f"{k} {v['detected']}/{v['applicable']}" for k, v in st["corruptions"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
