"""Segmented judging of long answers: planning, coverage, evidence integrity, aggregation, failure handling (all mocked)."""
import ast
import html
import json
import re

import httpx

from controlshift.evaluation import judge as jg
from controlshift.evaluation import judge_segments as seg
from controlshift.evaluation.judge_run import Budgeted, Pacer
from controlshift.generation.provider import GroqProvider, ProviderFailure

CTRL = [f"GV.SC-{i:02d}" for i in range(1, 10)]
EVIDENCE = {f"chunk:csf2.0:subcategory:{c}": f"{c} is a CSF 2.0 outcome about supply chain risk management." for c in CTRL}
EVIDENCE |= {f"xwalk:row{20 + i}": f"Official crosswalk row {20 + i}: CSF 2.0 {c} -> CSF 1.1 ID.SC-1" for i, c in enumerate(CTRL)}
GOLD = {"question_id": "T", "expected_facts": [{"statement": "GOLD-ONLY-FACT statement", "evidence": "x", "quote": None}]}
QUESTION = "How did supply chain risk management change?"


def long_answer():
    """17 units shaped like the saved B01 answer: 5 sentences, 3 key changes, 9 mappings."""
    sents = ["CSF 1.1 covers supply chain risk under ID.SC.", "CSF 2.0 expands this into the Govern function.",
             "GV.SC-01 is the programme-level outcome.", "Several outcomes now cover suppliers.", "Details follow in the mappings."]
    return {"answer": " ".join(sents),
            "key_changes": [{"statement": f"Change {i} concerns {CTRL[i]}.", "citations": [f"xwalk:row{20 + i}"]} for i in range(3)],
            "mappings": [{"focal_id": c, "reference_id": "ID.SC-1", "note": f"Row {20 + i}.", "citations": [f"xwalk:row{20 + i}"]}
                         for i, c in enumerate(CTRL)],
            "citations": [f"chunk:csf2.0:subcategory:{c}" for c in CTRL] + [f"xwalk:row{20 + i}" for i in range(9)],
            "abstained": False}


class SmartJudge:
    """Answers segmented prompts by reading the unit/evidence/citation lists out of the prompt (like a perfect, lazy judge)."""
    name, model = "fake", "smart-judge"

    def __init__(self, verdicts=None, fail_on_call=None, holistic=(4, 3, 2, 5), bad_batch=None, fail_holistic=False):
        self.verdicts, self.fail_on_call, self.holistic = verdicts or {}, fail_on_call, holistic
        self.bad_batch, self.fail_holistic = bad_batch, fail_holistic
        self.calls, self.prompts, self.systems, self.schemas, self.last_usage = 0, [], [], [], None

    def generate_structured(self, system, prompt, schema, name):
        self.schemas.append(name)
        return self.generate(system, prompt)

    def generate(self, system, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        self.systems.append(system)
        if self.fail_on_call == self.calls:
            raise ProviderFailure("Groq returned HTTP 429 (rate_limit_exceeded)")
        self.last_usage = {"prompt_tokens": 100, "output_tokens": 50, "reasoning_tokens": 10, "total_tokens": 150}
        if "holistic pass" in system:
            if self.fail_holistic:
                raise ProviderFailure("Groq returned HTTP 503")
            r, f, c, s = self.holistic
            d = lambda n: {"score": n, "justification": "j"}
            return json.dumps({"answer_relevance": d(r), "factual_correctness": d(f), "completeness": d(c), "citation_support": d(s)})
        unit_ids = ast.literal_eval(re.search(r"^Unit ids: (\[.*\])$", prompt, re.MULTILINE).group(1))
        ev_ids = ast.literal_eval(re.search(r"^Supplied evidence ids: (\[.*\])$", prompt, re.MULTILINE).group(1))
        block = prompt.split("CITATIONS TO ASSESS IN THIS REQUEST:")[1].split("EVIDENCE (untrusted")[0]
        cites = [ln.split(":", 1)[0] if not ln.startswith(("chunk:", "xwalk:")) else re.match(r"(\S+?): attached", ln).group(1)
                 for ln in block.strip().splitlines() if "attached to" in ln]
        if self.bad_batch == self.calls:
            unit_ids = unit_ids[:-1]                                  # omit a unit: must be rejected
        claims = []
        for u in unit_ids:
            v = self.verdicts.get(u, "supported")
            claims.append({"claim": f"claim for {u}", "unit_ids": [u], "evidence_ids": [ev_ids[0]] if v == "supported" else [],
                           "verdict": v, "justification": "j"})
        return json.dumps({"claims": claims, "non_factual_units": [],
                           "citation_assessments": [{"citation_id": c, "verdict": "supports", "justification": "j"} for c in cites]})


def run(judge, **kw):
    return seg.judge_answer_segmented(judge, QUESTION, GOLD, long_answer(), EVIDENCE, **kw)


# ---- planning / coverage -------------------------------------------------------------------------------
def test_plan_covers_every_unit_and_citation_exactly_once_in_order():
    ans = long_answer()
    units = [u["unit_id"] for u in jg.answer_units(ans)]
    assert len(units) == 17
    plan = seg.plan_batches(QUESTION, ans, EVIDENCE)
    flat = [u for b in plan for u in b["unit_ids"]]
    assert flat == units and all(1 <= len(b["unit_ids"]) <= seg.DEFAULT_BATCH_SIZE for b in plan)
    assert len(plan) >= 5
    assigned = [c for b in plan for c in b["citation_ids"]]
    assert sorted(assigned) == sorted(jg._cited(ans)) and len(assigned) == len(set(assigned))
    assert [b["batch_id"] for b in plan] == [f"B{i}" for i in range(1, len(plan) + 1)]
    assert seg.plan_batches(QUESTION, ans, EVIDENCE) == plan                       # deterministic


def test_batch_evidence_is_a_subset_of_the_supplied_evidence_and_texts_are_unaltered():
    ans = long_answer()
    j = SmartJudge()
    run(j)
    for b, prompt in zip(seg.plan_batches(QUESTION, ans, EVIDENCE), j.prompts, strict=False):
        assert set(b["evidence_ids"]) <= set(EVIDENCE)
        for e in b["evidence_ids"]:
            assert f'<evidence id="{e}">{html.escape(EVIDENCE[e], quote=False)}</evidence>' in prompt           # identical text, same id
        for e in set(EVIDENCE) - set(b["evidence_ids"]):
            assert f'<evidence id="{e}">' not in prompt                               # nothing outside the batch's subset
    # an id the generator never saw can never enter a batch: drop half of the evidence and re-plan
    kept = dict(list(EVIDENCE.items())[::2])
    for b in seg.plan_batches(QUESTION, ans, kept):
        assert set(b["evidence_ids"]) <= set(kept) and "ghost" not in b["prompt"]


def test_batch_prompts_hold_only_their_units_and_never_the_gold_facts():
    j = SmartJudge()
    run(j)
    batch_prompts = j.prompts[:-1]
    assert all("GOLD-ONLY-FACT" not in p for p in batch_prompts)                      # faithfulness stays evidence-only
    assert "GOLD-ONLY-FACT" in j.prompts[-1]                                          # the holistic call may use gold facts
    plan = seg.plan_batches(QUESTION, long_answer(), EVIDENCE)
    first, last = plan[0], plan[-1]
    assert f"Unit ids: {first['unit_ids']}" in batch_prompts[0] and f"Unit ids: {last['unit_ids']}" in batch_prompts[-1]
    assert last["unit_ids"][0] not in re.search(r"^Unit ids: (\[.*\])$", batch_prompts[0], re.MULTILINE).group(1)


def test_schemas_and_mode_markers():
    for sch in (seg.batch_json_schema(), seg.holistic_json_schema()):
        def walk(s):
            assert set(s) <= {"type", "properties", "required", "additionalProperties", "items", "enum"}
            if s["type"] == "object":
                assert s["additionalProperties"] is False and s["required"] == list(s["properties"])
                [walk(v) for v in s["properties"].values()]
            if s["type"] == "array":
                walk(s["items"])
        walk(sch)
    assert set(seg.batch_json_schema()["properties"]) == {"claims", "non_factual_units", "citation_assessments"}
    assert set(seg.holistic_json_schema()["properties"]) == set(jg.SCORED_DIMENSIONS)


# ---- complete runs, scoring ---------------------------------------------------------------------------------
def test_complete_segmented_judgment_derives_faithfulness_and_uses_holistic_scores_unaveraged():
    j = SmartJudge(holistic=(4, 3, 2, 5))
    res = run(j)
    assert res.status == "judged" and res.mode == "segmented" and res.limitations
    n_batches = len(seg.plan_batches(QUESTION, long_answer(), EVIDENCE))
    assert res.attempts == j.calls == n_batches + 1                                   # batches + one holistic call
    assert j.schemas == ["judge_batch"] * n_batches + ["judge_holistic"]
    f = res.derived["faithfulness"]
    assert f["factual_units"] == 17 and f["supported_units"] == 17 and f["score_1_5"] == 5
    assert jg.numeric_scores(res.derived) == {"faithfulness": 5, "answer_relevance": 4, "factual_correctness": 3,
                                              "completeness": 2, "citation_support": 5}
    assert res.derived["citation_verdicts"] == {"supports": 18}
    assert [b["status"] for b in res.batches] == ["judged"] * (n_batches + 1) and res.batches[-1]["batch_id"] == "H"
    assert res.batches[0]["tokens"]["total_tokens"] == 150


def test_unsupported_and_unclear_claims_are_kept_and_counted():
    res = run(SmartJudge(verdicts={"M2": "unsupported", "K1": "unclear"}))
    f = res.derived["faithfulness"]
    assert (f["supported_units"], f["unsupported_units"], f["unclear_units"]) == (15, 1, 1)
    assert f["unit_verdicts"]["M2"] == "unsupported" and f["unit_verdicts"]["K1"] == "unclear" and f["score_1_5"] == 5
    assert f["claims"] == 17 and f["unsupported"] == 1 and f["unclear"] == 1


# ---- failures ---------------------------------------------------------------------------------------------------
def test_provider_error_in_a_batch_makes_the_judgment_incomplete_and_stops_without_retry():
    j = SmartJudge(fail_on_call=2)
    res = run(j)
    assert res.status == "incomplete" and res.derived is None and res.output is None
    statuses = [b["status"] for b in res.batches]
    assert statuses[:2] == ["judged", "provider_error"] and set(statuses[2:]) == {"not_attempted"}
    assert j.calls == 2 and "429" in res.batches[1]["errors"][0]


def test_rejected_batch_output_is_incomplete_not_repaired_or_imputed():
    j = SmartJudge(bad_batch=1)
    res = run(j)
    assert res.status == "incomplete" and res.batches[0]["status"] == "invalid_output" and j.calls == 1
    assert any("not accounted for" in e for e in res.batches[0]["errors"]) and res.derived is None


def test_holistic_failure_leaves_the_judgment_incomplete_with_batches_kept():
    res = run(SmartJudge(fail_holistic=True))
    assert res.status == "incomplete" and res.derived is None and res.batches[-1]["status"] == "provider_error"
    assert all(b["status"] == "judged" for b in res.batches[:-1])


def test_request_limit_then_resume_repeats_no_completed_batch():
    first = SmartJudge()
    part = run(first, max_requests=1)
    assert part.status == "incomplete" and first.calls == 1
    assert [b["status"] for b in part.batches][:2] == ["judged", "not_attempted"]
    prior = {b["batch_id"]: b for b in part.batches if b["status"] == "judged"}
    second = SmartJudge()
    done = run(second, prior_batches=prior)
    n = len(seg.plan_batches(QUESTION, long_answer(), EVIDENCE))
    assert done.status == "judged" and second.calls == n                              # (n-1 remaining batches) + holistic
    assert done.batches[0].get("reused_from_prior_run") is True
    assert done.derived["faithfulness"]["factual_units"] == 17
    stale = {"B1": dict(prior["B1"], unit_ids=["S1"])}                                  # a changed plan never reuses a batch
    assert not run(SmartJudge(), prior_batches=stale).batches[0].get("reused_from_prior_run")


def test_non_answers_and_missing_judge_are_skipped():
    assert seg.judge_answer_segmented(None, QUESTION, GOLD, long_answer(), EVIDENCE).status == "skipped"
    assert seg.judge_answer_segmented(SmartJudge(), QUESTION, GOLD, {"abstained": True}, EVIDENCE).status == "skipped"


# ---- aggregation ---------------------------------------------------------------------------------------------------
def test_aggregation_counts_only_complete_judgments():
    ok, bad = run(SmartJudge()), run(SmartJudge(fail_on_call=1))
    agg = jg.aggregate_judgments({"A": {"judgment": ok.to_dict()}, "B": {"judgment": bad.to_dict()}})
    assert agg["judged"] == 1 and agg["status_counts"] == {"incomplete": 1, "judged": 1}
    assert agg["dimensions"]["faithfulness"]["n"] == 1 and agg["units"]["factual_units"] == 17


# ---- token budgeting -------------------------------------------------------------------------------------------------
def test_token_budgeting_splits_further_and_flags_units_that_cannot_fit():
    ans = long_answer()
    normal = seg.plan_batches(QUESTION, ans, EVIDENCE, batch_size=17, token_budget=6500)
    assert all(b["estimated_tokens"] <= 6500 or len(b["unit_ids"]) == 1 for b in normal)
    assert max(len(b["unit_ids"]) for b in normal) <= 17 and len(normal) > 1                 # the budget, not batch_size, split it
    tiny = seg.plan_batches(QUESTION, ans, EVIDENCE, batch_size=17, token_budget=500)
    assert len(tiny) == 17 and all(len(b["unit_ids"]) == 1 and b["over_budget"] for b in tiny)
    assert [u for b in tiny for u in b["unit_ids"]] == [u["unit_id"] for u in jg.answer_units(ans)]
    single = jg.build_judge_prompt(QUESTION, GOLD, ans, EVIDENCE)
    assert seg.estimate_tokens(jg.SYSTEM_PROMPT, single, jg.judge_json_schema(), 17, 21) > 8000   # why one call cannot fit 8k TPM


# ---- rate limits, budgets, pacing in the runner -----------------------------------------------------------------------
def test_budgeted_judge_counts_every_segmented_request_and_paces_them():
    sleeps = []
    pacer = Pacer(75, sleeps.append)
    inner = SmartJudge()
    b = Budgeted(inner, 3, pacer)
    res = run(b)
    assert res.status == "incomplete" and b.made == 3 and inner.calls == 3             # budget exhausted: no 4th request
    assert sleeps == [75, 75] and res.batches[3]["status"] == "provider_error"
    assert "request_budget_exhausted" in res.batches[3]["errors"][0]


# ---- provider ------------------------------------------------------------------------------------------------------------
def test_groq_generate_structured_sends_the_given_strict_schema_for_that_call_only():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})

    p = GroqProvider("k", "openai/gpt-oss-120b", 5, client=httpx.Client(transport=httpx.MockTransport(handler)),
                     json_schema=jg.judge_json_schema(), schema_name="judge_output")
    p.generate_structured("S", "P", seg.batch_json_schema(), "judge_batch")
    p.generate("S", "P")
    assert seen[0]["response_format"]["json_schema"]["name"] == "judge_batch"
    assert seen[0]["response_format"]["json_schema"]["schema"] == seg.batch_json_schema()
    assert seen[1]["response_format"]["json_schema"]["name"] == "judge_output"             # the default is untouched
