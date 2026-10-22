"""Groq as the answer GENERATOR (Qwen) with a separate Groq judge (GPT-OSS). All HTTP is mocked."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from controlshift.api.app import create_app
from controlshift.api.services import Services
from controlshift.evaluation import judge as jg
from controlshift.evaluation.judge import JudgeSettings, judge_provider
from controlshift.evaluation.judge_run import Budgeted
from controlshift.evidence.assemble import EvidenceAssembler
from controlshift.generation.config import Settings
from controlshift.generation.generate import ANSWERED, GroundedGenerator
from controlshift.generation.provider import (
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    ProviderFailure,
    ProviderNotConfigured,
    provider_from_settings,
)
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.store.queries import KnowledgeStore
from fakes import answer

KEY = "gsk_SECRET_GENERATOR_KEY_789"
QWEN, GPT = "qwen/qwen3.8-27b", "openai/gpt-oss-120b"
GV_SC_03 = "chunk:csf2.0:subcategory:GV.SC-03"


def qwen(handler, **kw):
    return GroqProvider(KEY, QWEN, 5, client=httpx.Client(transport=httpx.MockTransport(handler)), **kw)


def chat(content, model=QWEN, finish="stop"):
    return {"model": model, "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": finish}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 200, "total_tokens": 1100,
                      "completion_tokens_details": {"reasoning_tokens": 120}}}


# ---- configuration and selection -------------------------------------------------------------------
ENV = {"LLM_PROVIDER": "groq", "GROQ_MODEL": QWEN, "JUDGE_PROVIDER": "groq", "JUDGE_MODEL": GPT, "JUDGE_API_KEY": KEY,
       "GEMINI_API_KEY": "g", "GEMINI_MODEL": "gemini-3.8-flash", "MISTRAL_API_KEY": "m", "MISTRAL_MODEL": "mistral-small-latest"}


def test_settings_resolve_generator_and_judge_models_separately():
    s = Settings.from_env(ENV)
    assert s.llm_provider == "groq" and s.groq_model == QWEN and s.groq_api_key == KEY
    assert KEY not in repr(s)
    g, j = provider_from_settings(s), judge_provider(JudgeSettings.from_env(ENV))
    assert isinstance(g, GroqProvider) and isinstance(j, GroqProvider)
    assert (g.model, j.model) == (QWEN, GPT) and g is not j


def test_generator_key_does_not_come_from_other_providers_and_model_is_required():
    no_judge_key = {k: v for k, v in ENV.items() if k != "JUDGE_API_KEY"}
    assert provider_from_settings(Settings.from_env(no_judge_key)) is None            # Gemini/Mistral keys are never reused
    assert Settings.from_env(no_judge_key | {"GROQ_API_KEY": KEY}).groq_api_key == KEY
    assert provider_from_settings(Settings.from_env(ENV | {"GROQ_MODEL": ""})) is None
    non_groq_judge = ENV | {"JUDGE_PROVIDER": "gemini"}
    assert Settings.from_env(non_groq_judge).groq_api_key is None                     # a Gemini judge's key is not a Groq key
    with pytest.raises(ProviderNotConfigured):
        GroqProvider.from_settings(Settings.from_env(ENV | {"LLM_PROVIDER": "gemini"}))


def test_other_providers_remain_selectable():
    assert isinstance(provider_from_settings(Settings.from_env(ENV | {"LLM_PROVIDER": "gemini"})), GeminiProvider)
    assert isinstance(provider_from_settings(Settings.from_env(ENV | {"LLM_PROVIDER": "mistral"})), MistralProvider)
    assert provider_from_settings(Settings.from_env({})) is None       # default gemini, nothing configured


# ---- request / response -----------------------------------------------------------------------------
def test_request_shape_reasoning_format_only_when_set_and_think_text_stripped():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=chat('<think>let me reason</think>{"ok": true}'))

    p = qwen(handler)
    assert p.generate("S", "P") == '{"ok": true}'
    b = seen[0]
    assert b["model"] == QWEN and b["temperature"] == 0 and b["response_format"] == {"type": "json_object"}
    assert "reasoning_format" not in b
    assert p.last_model == QWEN and p.last_usage == {"prompt_tokens": 900, "output_tokens": 200, "reasoning_tokens": 120,
                                                     "total_tokens": 1100}
    qwen(handler, reasoning_format="hidden").generate("S", "P")
    assert seen[1]["reasoning_format"] == "hidden"
    only_think = qwen(lambda r: httpx.Response(200, json=chat("<think>no answer</think>")))
    with pytest.raises(ProviderFailure, match="empty"):
        only_think.generate("S", "P")


def test_errors_leak_no_key():
    p = qwen(lambda r: httpx.Response(429, json={"error": {"message": KEY, "code": "rate_limit_exceeded"}}))
    with pytest.raises(ProviderFailure) as exc:
        p.generate("S", "P")
    assert "HTTP 429 (rate_limit_exceeded)" in str(exc.value) and KEY not in str(exc.value)


# ---- pipeline, API ----------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def store(real_db):
    with KnowledgeStore(real_db[0]) as s:
        yield s


@pytest.fixture(scope="module")
def search(real_db):
    return BM25Index.build(load_corpus(real_db[0])).search


def test_qwen_output_goes_through_unchanged_validation(store, search):
    bundle = EvidenceAssembler(store, search, "bm25").assemble("What does GV.SC-03 require?")
    ok = qwen(lambda r: httpx.Response(200, json=chat(json.dumps(answer([GV_SC_03])))))
    assert GroundedGenerator(ok, Settings()).generate(bundle, store).status == ANSWERED
    bad = qwen(lambda r: httpx.Response(200, json=chat(json.dumps(answer(["chunk:csf2.0:subcategory:NOPE-1"])))))
    res = GroundedGenerator(bad, Settings(max_llm_attempts=1)).generate(bundle, store)
    assert res.status != ANSWERED and res.answer is None
    fenced = qwen(lambda r: httpx.Response(200, json=chat("not json")))
    assert GroundedGenerator(fenced, Settings(max_llm_attempts=1)).generate(bundle, store).answer is None


def test_fastapi_ask_uses_the_selected_groq_generator(real_db, search):
    provider = qwen(lambda r: httpx.Response(200, json=chat(json.dumps(answer([GV_SC_03])))))
    s = Settings(db_path=real_db[0], llm_provider="groq", groq_api_key=KEY, groq_model=QWEN)
    with TestClient(create_app(lambda: Services(real_db[0], s, search, "bm25", provider, [])),
                    raise_server_exceptions=False) as c:
        assert c.get("/health").json()["llm"] == {"configured": True, "provider": "groq", "model": QWEN}
        r = c.post("/ask", json={"question": "What does GV.SC-03 require?"})
        body = r.json()
        assert r.status_code == 200 and body["status"] == ANSWERED and body["provider"] == {"name": "groq", "model": QWEN}
        assert KEY not in r.text and KEY not in c.get("/health").text


# ---- evaluation runner: separate models, budgets and disclosure ---------------------------------------
def test_independence_note_discloses_shared_infrastructure_but_different_families():
    note = jg.independence_note({"name": "groq", "model": QWEN}, {"name": "groq", "model": GPT})
    assert "different model families" in note and "SAME provider infrastructure" in note and "not ground truth" in note
    same_vendor = jg.independence_note({"name": "groq", "model": "openai/gpt-oss-20b"}, {"name": "groq", "model": GPT})
    assert "SAME provider family" in same_vendor
    assert "SAME model" in jg.independence_note({"name": "groq", "model": GPT}, {"name": "groq", "model": GPT})
    assert "different providers" in jg.independence_note({"name": "gemini", "model": "a"}, {"name": "groq", "model": GPT})


def test_budgeted_generator_and_judge_budgets_are_independent():
    gen = Budgeted(qwen(lambda r: httpx.Response(200, json=chat("{}"))), 1)
    jud = Budgeted(GroqProvider(KEY, GPT, 5, client=httpx.Client(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=chat("{}", model=GPT))))), 1)
    gen.generate("s", "p"), jud.generate("s", "p")
    with pytest.raises(ProviderFailure):
        gen.generate("s", "p")
    assert (gen.made, jud.made) == (1, 1) and gen.resolved_models == [QWEN] and jud.resolved_models == [GPT]
    assert gen.model != jud.model
