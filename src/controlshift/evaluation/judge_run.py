"""Orchestrates generation + deterministic checks + LLM judging for a gold subset.

Safe by construction: hard request budgets for generator and judge separately, no automatic retries,
stop on the first provider error, and a result envelope that says whether the generator was a real
provider or a stand-in, so mocked runs can never be reported as live accuracy.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from statistics import mean, median

from ..evidence.assemble import EvidenceAssembler
from ..generation.config import Settings
from ..generation.context import build_context
from ..generation.generate import GroundedGenerator
from ..generation.provider import LLMProvider, ProviderError, ProviderFailure
from .answers import SEMANTIC, aggregate, check_answer
from .judge import (
    RUBRIC_VERSION,
    JudgeSettings,
    aggregate_judgments,
    independence_note,
    judge_answer,
)

SUBSET_SIX = ["A01", "B01", "C01", "F01", "E01", "H02"]  # one per required question type
LIVE_PROVIDERS = {"gemini", "groq", "mistral"}


class BudgetExhausted(ProviderFailure):
    code = "request_budget_exhausted"


class Budgeted:
    """Counts requests to a provider and refuses to exceed the budget (budget 0 = never call)."""

    def __init__(self, provider: LLMProvider | None, budget: int):
        self.provider, self.budget, self.made = provider, budget, 0
        self.name = getattr(provider, "name", None)
        self.model = getattr(provider, "model", None)
        self.resolved_models: list[str] = []  # model ids the API actually reported (distinct, in order)
        self.usage_log: list[dict] = []  # token counts per successful response

    def tokens_since(self, n: int) -> dict | None:
        rows = self.usage_log[n:]
        return {k: sum(r.get(k) or 0 for r in rows) for k in ("prompt_tokens", "output_tokens", "reasoning_tokens", "total_tokens")} if rows else None

    def generate(self, system: str, prompt: str) -> str:
        if self.provider is None or self.made >= self.budget:
            raise BudgetExhausted("request budget exhausted; no request was sent")
        self.made += 1
        text = self.provider.generate(system, prompt)
        served = getattr(self.provider, "last_model", None)
        if served and served not in self.resolved_models:
            self.resolved_models.append(served)
        if getattr(self.provider, "last_usage", None):
            self.usage_log.append(dict(self.provider.last_usage))
        return text


def select_questions(gold: list[dict], subset: str) -> list[dict]:
    valid = [g for g in gold if not g.get("invalid_input")]
    if subset == "all":
        return valid
    if subset == "six":
        by = {g["question_id"]: g for g in valid}
        return [by[q] for q in SUBSET_SIX]
    raise ValueError("subset must be 'six' or 'all'")


def plan(questions: list[dict]) -> dict:
    """Maximum real requests a live run could make (upper bound; no calls are made here)."""
    return {"questions": [q["question_id"] for q in questions], "max_generation_requests": len(questions),
            "max_judge_requests": len(questions), "max_total_requests": 2 * len(questions)}


def _evidence_texts(bundle, ctx) -> dict[str, str]:
    """Plain text of every evidence item the generator was shown (keyed by citation id)."""
    out = {}
    for r in bundle.control_records + bundle.passages:
        if r["citation_id"] in ctx.allowed_citations:
            out[r["citation_id"]] = r["text"]
    for r in bundle.crosswalk_records:
        if r["citation_id"] in ctx.allowed_citations:
            out[r["citation_id"]] = (f"Official crosswalk row {r['excel_row']}: CSF 2.0 {r['focal_id']} "
                                     f"({r['focal_description']}) -> CSF 1.1 {r['reference_id'] or 'NO REFERENCE'} "
                                     f"({r['reference_description'] or ''}); mapping_type={r['mapping_type']}; "
                                     f"comments={r['comments'] or ''}")
    return out


def _lat(xs: list[float]) -> dict:
    return {"n": len(xs), "mean_s": mean(xs), "median_s": median(xs), "max_s": max(xs)} if xs else {"n": 0}


def run_judged_evaluation(questions: list[dict], assembler: EvidenceAssembler, store, generator: LLMProvider | None,
                          judge: LLMProvider | None, settings: Settings, judge_settings: JudgeSettings,
                          max_generation_requests: int, max_judge_requests: int,
                          clock: Callable[[], float] = time.perf_counter, pause_seconds: float = 0.0,
                          sleep: Callable[[float], None] = time.sleep) -> dict:
    gen, jdg = Budgeted(generator, max_generation_requests), Budgeted(judge, max_judge_requests)
    gen_meta = {"name": gen.name, "model": gen.model}
    jdg_meta = {"name": jdg.name, "model": jdg.model}
    records: dict[str, dict] = {}
    stopped = None
    for n, g in enumerate(questions):
        qid = g["question_id"]
        if n and pause_seconds > 0 and not stopped:
            sleep(pause_seconds)  # spreads requests out to respect per-minute token limits (no extra requests)
        if stopped:
            records[qid] = {"category": g["category"], "question": g["question"], "generation": {
                "status": "not_attempted", "reason": stopped}, "deterministic": None, "judgment": None}
            continue
        t0 = clock()
        g_n, j_n = len(gen.usage_log), len(jdg.usage_log)
        bundle = assembler.assemble(g["question"])
        ctx = build_context(bundle, settings.context_chars, settings.max_passage_chars)
        rec = {"category": g["category"], "question": g["question"], "judgment": None, "deterministic": None,
               "evidence_supplied": _evidence_texts(bundle, ctx)}  # exactly what the generator and judge were shown
        try:
            res = GroundedGenerator(gen, settings).generate(bundle, store)
        except ProviderError as exc:  # timeouts as well as HTTP failures: record and stop, never crash
            stopped = f"provider error on {qid}: {exc.code}"
            rec["generation"] = {"status": "provider_error", "error": f"{exc.code}: {exc}"}
            rec["latency_s"] = {"generation": round(clock() - t0, 3)}
            records[qid] = rec
            continue
        gen_s = clock() - t0
        rec["tokens"] = {"generation": gen.tokens_since(g_n)}
        rec["generation"] = {"status": res.status, "attempts": res.attempts, "rejection": res.rejection,
                             "warnings": res.warnings, "system_uncertainties": res.system_uncertainties,
                             "abstention_reason": res.abstention_reason, "answer": res.answer}
        answer = res.answer if res.answer is not None else (
            {"answer": "", "abstained": True, "abstention_reason": res.abstention_reason}
            if res.status == "abstained" else None)
        if answer is not None:
            checks = check_answer(answer, g, store.conn, set(bundle.citations))
            rec["deterministic"] = {"checks": checks, "all_passed": all(c["status"] != "fail" for c in checks)}
        j_s = 0.0
        if res.status == "answered":
            tj = clock()
            jud = judge_answer(jdg if judge is not None else None, g["question"], g, res.answer,
                               _evidence_texts(bundle, ctx), judge_settings.max_attempts)
            j_s = clock() - tj
            rec["judgment"] = jud.to_dict()
            rec["tokens"]["judge"] = jdg.tokens_since(j_n)
            if jud.status == "provider_error":
                stopped = f"judge provider error on {qid}"
        rec["latency_s"] = {"generation": round(gen_s, 3), "judge": round(j_s, 3),
                            "end_to_end": round(gen_s + j_s, 3)}
        records[qid] = rec

    attempted = {q: r for q, r in records.items() if r.get("deterministic")}
    is_live = (gen.name in LIVE_PROVIDERS) and (gen.model is not None)
    judge_live = (jdg.name in LIVE_PROVIDERS) and (jdg.model is not None)
    return {
        "kind": "real_generator" if is_live else "mocked_or_missing_generator",
        "judge_kind": "live_llm_judge" if judge_live else "mocked_or_missing_judge",
        "generator": {**gen_meta, "resolved_models": gen.resolved_models},
        "judge": {**jdg_meta, "resolved_models": jdg.resolved_models}, "rubric_version": RUBRIC_VERSION,
        "independence_note": independence_note(gen_meta, jdg_meta) if gen.name and jdg.name else
        "No judge configured; no judge scores exist.",
        "status": "stopped_on_provider_error" if stopped else "complete", "stopped_reason": stopped,
        "budgets": {"max_generation_requests": max_generation_requests, "generation_requests_made": gen.made,
                    "max_judge_requests": max_judge_requests, "judge_requests_made": jdg.made,
                    "automatic_retries": False},
        "questions_requested": [g["question_id"] for g in questions],
        "per_question": records,
        "deterministic_aggregate": aggregate({q: {"category": r["category"], "checks": r["deterministic"]["checks"],
                                                  "all_passed": r["deterministic"]["all_passed"]}
                                              for q, r in attempted.items()}) if attempted else None,
        "judge_aggregate": aggregate_judgments(records),
        "latency": {"generation": _lat([r["latency_s"]["generation"] for r in records.values()
                                        if r.get("latency_s") and "generation" in r["latency_s"]
                                        and r["generation"]["status"] != "provider_error"]),
                    "judge": _lat([r["latency_s"]["judge"] for r in records.values()
                                   if r.get("latency_s") and r.get("judgment") and r["judgment"]["status"] == "judged"]),
                    "end_to_end": _lat([r["latency_s"]["end_to_end"] for r in records.values()
                                        if r.get("latency_s") and "end_to_end" in r["latency_s"]])},
        "semantic_faithfulness": SEMANTIC,
        "warnings": ["Sample too small to be a statistically meaningful accuracy benchmark."]
        if len(questions) < 30 else [],
    }
