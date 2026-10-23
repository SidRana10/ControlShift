"""Readable human-review report of the six live RAG answers (A01, B01, C01, F01, E01, H02).

No API calls. Reads saved live artifacts (generation + deterministic checks + the evidence the generator was shown) and the
gold file, and writes eval/live_answer_review.md. It shows deterministic findings separately from semantic questions that a
human must still answer, and invents no scores. LLM-judge output is deliberately not included.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from controlshift.evaluation.judge import answer_units
from controlshift.evaluation.judge_segments import unit_citations

EVAL = Path(__file__).parent
SOURCES = [EVAL / "live_runs" / "2026-10-22_six_question_qwen_gptoss_partial_stopped_at_B01.json",
           EVAL / "live_runs" / "2026-10-22_generation_C01_F01_E01_H02.json"]
ORDER = ["A01", "B01", "C01", "F01", "E01", "H02"]
NOTE = {"B01": "Generation latency includes a 75 s pacing wait before the request; the API call itself took a few seconds."}


def load_records() -> tuple[dict, dict]:
    recs, runs = {}, {}
    for src in SOURCES:
        if src.is_file():
            run = json.loads(src.read_text(encoding="utf-8"))
            for q, r in run["per_question"].items():
                if r["generation"]["status"] != "not_attempted" and q not in recs:
                    recs[q] = r
                    runs[q] = {"file": src.name, "generator": run["generator"]}
    return recs, runs


def _clip(text: str, n: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def render(gold: dict, recs: dict, runs: dict) -> str:
    L = ["# Live RAG answer review (six-question exploratory sample)", "",
         "Everything below was produced by the real ControlShift pipeline (hybrid retrieval -> evidence assembly -> Groq `qwen/qwen3.8-27b`). "
         "**Deterministic findings** (schema, citation ids, official crosswalk rows, versions, abstention) are machine-checked. "
         "**Semantic quality is NOT assessed here**: whether each statement is faithful to its cited text, and whether the answer is correct "
         "and complete, are `PENDING` human review. No accuracy, faithfulness or correctness score is given or implied; six questions "
         "are a small exploratory sample. LLM-judge output is not part of this report. **Data note:** the original crosswalk workbook has no `mapping_type` column; "
         "`mapped` / `new_in_2_0` are ControlShift-derived labels (reference present / no reference with a \"new\" comment). No independent human review has been performed.", ""]
    L += ["| Question | Category | Answer status | Deterministic checks | Human review |", "|---|---|---|---|---|"]
    for q in ORDER:
        r = recs.get(q)
        if not r:
            L.append(f"| {q} | {gold[q]['category']} | not generated | n/a | PENDING |")
            continue
        d = r.get("deterministic")
        failed = [c["name"] for c in d["checks"] if c["status"] == "fail"] if d else []
        L.append(f"| {q} | {r['category']} | {r['generation']['status']} | "
                 f"{'all applicable passed' if d and not failed else ('FAILED: ' + ', '.join(failed)) if d else 'n/a'} | PENDING |")
    for q in ORDER:
        g, r = gold[q], recs.get(q)
        L += ["", "---", "", f"## {q} — {g['category']}", "", f"**Question:** {g['question']}", ""]
        if not r:
            L += ["_Not generated._", "", "**Human review status:** PENDING"]
            continue
        gen, ev = r["generation"], r.get("evidence_supplied") or {}
        ans = gen.get("answer")
        L += ["### Actual output", ""]
        if ans and not ans.get("abstained"):
            L += [ans["answer"], ""]
            if ans.get("key_changes"):
                L += ["**Key changes**", ""] + [f"- {k['statement']} `{', '.join(k['citations'])}`" for k in ans["key_changes"]] + [""]
            if ans.get("mappings"):
                L += ["**Mappings**", ""] + [f"- {m['focal_id']} → {m.get('reference_id') or '(no CSF 1.1 reference)'} — {m.get('note', '')} "
                                             f"`{', '.join(m['citations'])}`" for m in ans["mappings"]] + [""]
            for key, title in (("uncertainties", "Uncertainties stated by the answer"), ("unresolved_questions", "Unresolved questions")):
                if ans.get(key):
                    L += [f"**{title}**", ""] + [f"- {x}" for x in ans[key]] + [""]
            L += [f"**Answer-level citations:** {', '.join(f'`{c}`' for c in ans.get('citations', [])) or 'none'}", ""]
        elif ans:
            L += [f"**ABSTAINED.** Reason given: {ans.get('abstention_reason')}", ""]
        elif gen.get("abstention_reason") or gen["status"] == "abstained":
            L += [f"**ABSTAINED (system).** {gen.get('abstention_reason')}", ""]
        else:
            L += [f"_No answer produced (status `{gen['status']}`): {gen.get('rejection') or gen.get('error') or ''}_", ""]

        L += ["### Evidence supplied to the generator", "",
              f"{len(ev)} items: " + (", ".join(f"`{k}`" for k in ev) or "none"), ""]
        cited = sorted({c for u in (answer_units(ans) if ans and not ans.get("abstained") else []) for c in unit_citations(ans).get(u["unit_id"], [])}
                       | set((ans or {}).get("citations", [])))
        if cited:
            L += ["<details><summary>Cited evidence text</summary>", ""] + [f"- `{c}`: {_clip(ev.get(c, '(not in evidence)'))}" for c in cited] + ["", "</details>", ""]

        L += ["### Expected (existing gold dataset; never shown to the generator)", ""]
        if g["must_abstain"]:
            L += [f"- Must abstain (basis: {g['abstention_basis']}). {g['abstention_conditions']}"]
        L += [f"- Expected crosswalk rows: {g['expected_crosswalk_rows'] or 'none'}"]
        maps = "; ".join("row {}: {} → {}".format(m["row"], m["focal"], m["reference"] or "(none)") for m in g["expected_mappings"])
        L += ["- Expected mappings: " + (maps or "none")]
        if g["conflict_rows"]:
            L += [f"- Conflict rows (both must be preserved): {g['conflict_rows']}"]
        if g["expect_new"]:
            L += [f"- Conceptually new in 2.0 (no CSF 1.1 reference): {g['expect_new']}"]
        L += ["- Expected facts: " + ("; ".join(f"{f['statement']} [{f.get('evidence')}]" for f in g["expected_facts"]) or "none")]

        L += ["", "### Deterministic validation (machine-checked)", ""]
        d = r.get("deterministic")
        if d:
            L += ["| Check | Result | Detail |", "|---|---|---|"] + [f"| {c['name']} | {c['status'].upper()} | {c['detail']} |" for c in d["checks"]]
        else:
            L += ["_Not run._"]
        exp_rows = [f"xwalk:row{x}" for x in g["expected_crosswalk_rows"]]
        if exp_rows:
            used = set((ans or {}).get("citations", [])) | {c for cs in unit_citations(ans or {}).values() for c in cs}
            missing = [x for x in exp_rows if x not in used]
            not_ret = [x for x in missing if x not in ev]
            L += ["", "**Expected rows missing from the answer:** " + (", ".join(f"`{x}`" for x in missing) or "none")]
            for x in not_ret:
                L += [f"- **RETRIEVAL FAILURE:** `{x}` was never in the evidence supplied to the generator, so the model could not cite it."]
            for x in [m for m in missing if m in ev]:
                L += [f"- Generation omission: `{x}` was supplied but not cited."]

        L += ["", "### Needs human verification (semantic; NOT assessed by any check)", ""]
        flags = []
        if ans and not ans.get("abstained"):
            ucs = unit_citations(ans)
            for u in answer_units(ans):
                cs = ucs.get(u["unit_id"])
                flags.append(f"- `{u['unit_id']}` {_clip(u['text'], 160)} — " + (f"cited: {', '.join(f'`{c}`' for c in cs)}" if cs else
                             "no citation attached to this sentence (check it against the answer-level citations)"))
            for m in ans.get("mappings", []):
                if not any(x["focal"] == m["focal_id"] and (x["reference"] or None) == (m.get("reference_id") or None) for x in g["expected_mappings"]):
                    flags.append(f"- Mapping {m['focal_id']} → {m.get('reference_id') or '(none)'} is not among the gold rows for this question; "
                                 "the official-mapping check passed, so it matches a real crosswalk row, but verify it is relevant.")
        elif g["must_abstain"]:
            flags.append("- Confirm the abstention reason is accurate and does not invent content.")
        L += flags or ["- (nothing generated)"]

        L += ["", "### Generation details", ""]
        tk = (r.get("tokens") or {}).get("generation")
        lat = (r.get("latency_s") or {}).get("generation")
        L += [f"- Generator: `{runs[q]['generator']['name']}` / `{runs[q]['generator']['model']}` (reported: {', '.join(runs[q]['generator'].get('resolved_models') or ['n/a'])})",
              "- Tokens: " + (f"{tk['prompt_tokens']} prompt + {tk['output_tokens']} output = {tk['total_tokens']}" if tk else "n/a (no provider request was needed or none recorded)"),
              "- Latency: " + (f"{lat} s" if lat is not None else "n/a") + (f" — {NOTE[q]}" if q in NOTE else ""),
              f"- Attempts: {gen.get('attempts')}; rejections: {gen.get('rejection') or 'none'}; warnings: {gen.get('warnings') or 'none'}",
              f"- Source artifact: `eval/live_runs/{runs[q]['file']}`", "", "**Human review status:** PENDING (reviewer: —)"]
    return "\n".join(L) + "\n"


def main() -> int:
    gold = {}
    for line in (EVAL / "answer_questions.jsonl").read_text(encoding="utf-8").splitlines():
        g = json.loads(line)
        gold[g["question_id"]] = g
    recs, runs = load_records()
    out = EVAL / "live_answer_review.md"
    out.write_text(render(gold, recs, runs), encoding="utf-8")
    print(f"wrote {out} ({len(recs)} of {len(ORDER)} questions have a generation record)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
