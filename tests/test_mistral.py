"""Mistral generator: request/response format, errors, provider selection, schema compatibility and API
integration. All HTTP is mocked (httpx.MockTransport); no real request is ever sent."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from controlshift.api.app import create_app
from controlshift.api.services import Services
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
    ProviderTimeout,
    provider_from_settings,
)
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.store.queries import KnowledgeStore
from fakes import answer

SECRET = "mk_SECRET_TEST_KEY_456"
GV_SC_03 = "chunk:csf2.0:subcategory:GV.SC-03"


def mistral(handler, model="mistral-small-latest", timeout=5):
    return MistralProvider(SECRET, model, timeout, client=httpx.Client(transport=httpx.MockTransport(handler)))


def chat(content, finish="stop", model="mistral-small-2506", usage=True):
    body = {"id": "x", "object": "chat.completion", "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": finish}]}
    if usage:
        body["usage"] = {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150}
    return body


# ---- request / response format ----------------------------------------------------------------------
def test_request_shape_and_response_parsing():
    seen = {}

    def handler(request):
        seen.update(url=str(request.url), auth=request.headers.get("authorization"), body=json.loads(request.content))
        return httpx.Response(200, json=chat('{"ok": true}'))

    p = mistral(handler)
    assert p.generate("SYS", "PROMPT") == '{"ok": true}'
    assert seen["url"] == "https://api.mistral.ai/v1/chat/completions" and SECRET not in seen["url"]
    assert seen["auth"] == f"Bearer {SECRET}"
    b = seen["body"]
    assert b["model"] == "mistral-small-latest" and b["temperature"] == 0
    assert b["response_format"] == {"type": "json_object"}
    assert b["messages"] == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "PROMPT"}]
    assert SECRET not in json.dumps(b)


def test_usage_and_resolved_model_are_recorded_and_alias_is_not_hidden():
    p = mistral(lambda r: httpx.Response(200, json=chat("{}")))
    assert p.last_usage is None and p.last_model is None
    p.generate("s", "p")
    assert p.model == "mistral-small-latest" and p.last_model == "mistral-small-2506"
    assert p.last_usage == {"prompt_tokens": 120, "output_tokens": 30, "reasoning_tokens": None, "total_tokens": 150}
    q = mistral(lambda r: httpx.Response(200, json=chat("{}", usage=False)))
    q.generate("s", "p")
    assert q.last_usage == {"prompt_tokens": None, "output_tokens": None, "reasoning_tokens": None, "total_tokens": None}


def test_chunked_content_is_joined():
    chunks = [{"type": "text", "text": '{"a": '}, {"type": "text", "text": "1}"}]
    assert mistral(lambda r: httpx.Response(200, json=chat(chunks))).generate("s", "p") == '{"a": 1}'


@pytest.mark.parametrize("handler,fragment", [
    (lambda r: httpx.Response(429, json={"object": "error", "message": f"slow {SECRET}", "type": "rate_limited", "code": "1"}),
     "HTTP 429 (rate_limited)"),
    (lambda r: httpx.Response(401, json={"message": "Unauthorized", "request_id": "abc"}), "HTTP 401"),
    (lambda r: httpx.Response(503, text=f"overloaded {SECRET}"), "HTTP 503"),
    (lambda r: httpx.Response(200, json={"choices": []}), "unusable"),
    (lambda r: httpx.Response(200, text="<html>"), "unusable"),
    (lambda r: httpx.Response(200, json=chat("   ")), "empty"),
    (lambda r: httpx.Response(200, json=chat(None)), "empty"),
    (lambda r: httpx.Response(200, json=chat('{"cut": ', finish="length")), "cut off"),
])
def test_failures_are_controlled_and_leak_nothing(handler, fragment):
    p = mistral(handler)
    with pytest.raises(ProviderFailure) as exc:
        p.generate("s", "p")
    assert fragment in str(exc.value) and SECRET not in str(exc.value) and SECRET not in repr(exc.value)
    assert p.last_usage is None  # nothing is recorded for a failed response


def test_timeout_and_connection_errors_name_no_url_or_key():
    def slow(request):
        raise httpx.ReadTimeout("t", request=request)

    def down(request):
        raise httpx.ConnectError(f"cannot reach https://api.mistral.ai {SECRET}", request=request)

    with pytest.raises(ProviderTimeout, match="Mistral request timed out"):
        mistral(slow).generate("s", "p")
    with pytest.raises(ProviderFailure) as exc:
        mistral(down).generate("s", "p")
    assert str(exc.value) == "Mistral request failed (ConnectError)" and SECRET not in str(exc.value)


def test_requires_key_and_model_and_never_sends_on_construction(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("no HTTP request may be made on construction")
    monkeypatch.setattr(httpx.Client, "send", boom)
    for key, model in (("", "m"), (SECRET, ""), ("", "")):
        with pytest.raises(ProviderNotConfigured):
            MistralProvider(key, model)
    assert MistralProvider(SECRET, "mistral-small-latest").name == "mistral"


# ---- configuration and provider selection -------------------------------------------------------------
def test_settings_defaults_to_gemini_and_never_prints_keys():
    s = Settings.from_env({})
    assert s.llm_provider == "gemini" and s.mistral_api_key is None and s.mistral_model is None
    s = Settings.from_env({"LLM_PROVIDER": "Mistral", "MISTRAL_API_KEY": SECRET, "MISTRAL_MODEL": "mistral-small-latest"})
    assert s.llm_provider == "mistral" and s.mistral_model == "mistral-small-latest"
    assert SECRET not in repr(s) and SECRET not in str(s)


def test_provider_selection():
    both = {"gemini_api_key": "g", "gemini_model": "gm", "mistral_api_key": SECRET,
            "mistral_model": "mistral-small-latest"}
    assert isinstance(provider_from_settings(Settings(llm_provider="gemini", **both)), GeminiProvider)
    assert isinstance(provider_from_settings(Settings(**both)), GeminiProvider)            # backward-compatible default
    m = provider_from_settings(Settings(llm_provider="mistral", **both))
    assert isinstance(m, MistralProvider) and m.model == "mistral-small-latest"
    # the selected provider's credentials are required; the other provider's are never used as a fallback
    assert provider_from_settings(Settings(llm_provider="mistral", gemini_api_key="g", gemini_model="gm")) is None
    assert provider_from_settings(Settings(llm_provider="gemini", mistral_api_key=SECRET, mistral_model="m")) is None
    assert provider_from_settings(Settings(llm_provider="unknown", **both)) is None


def test_judge_still_resolves_to_groq_whatever_the_generator():
    env = {"LLM_PROVIDER": "mistral", "MISTRAL_API_KEY": SECRET, "MISTRAL_MODEL": "mistral-small-latest",
           "GEMINI_API_KEY": "g", "JUDGE_PROVIDER": "groq", "JUDGE_MODEL": "openai/gpt-oss-120b", "JUDGE_API_KEY": "gsk_x"}
    j = judge_provider(JudgeSettings.from_env(env))
    assert isinstance(j, GroqProvider) and j.model == "openai/gpt-oss-120b"
    no_key = {k: v for k, v in env.items() if k != "JUDGE_API_KEY"}
    assert judge_provider(JudgeSettings.from_env(no_key)) is None        # Mistral's key is never reused for the judge


def test_example_env_documents_selection_without_credentials():
    from pathlib import Path
    text = (Path(__file__).parent.parent / ".env.example").read_text()
    assert "LLM_PROVIDER=gemini" in text and "gemini | mistral" in text
    for line in text.splitlines():
        if line.startswith(("MISTRAL_API_KEY=", "GEMINI_API_KEY=", "JUDGE_API_KEY=")):
            assert line.split("=", 1)[1].split("#")[0].strip() == ""


def test_budgeted_wrapper_records_resolved_model_once_and_usage():
    p = mistral(lambda r: httpx.Response(200, json=chat("{}")))
    b = Budgeted(p, 2)
    b.generate("s", "p"), b.generate("s", "p")
    assert b.resolved_models == ["mistral-small-2506"] and len(b.usage_log) == 2
    assert b.tokens_since(0)["total_tokens"] == 300 and b.tokens_since(1)["total_tokens"] == 150


# ---- schema compatibility and API integration ---------------------------------------------------------
@pytest.fixture(scope="module")
def store(real_db):
    with KnowledgeStore(real_db[0]) as s:
        yield s


@pytest.fixture(scope="module")
def search(real_db):
    return BM25Index.build(load_corpus(real_db[0])).search


def test_mistral_output_goes_through_the_unchanged_grounding_pipeline(store, search):
    bundle = EvidenceAssembler(store, search, "bm25").assemble("What does GV.SC-03 require?")
    good = answer([GV_SC_03])
    res = GroundedGenerator(mistral(lambda r: httpx.Response(200, json=chat(json.dumps(good)))), Settings()).generate(bundle, store)
    assert res.status == ANSWERED and res.attempts == 1 and GV_SC_03 in res.answer["citations"]
    # a fabricated citation is still rejected, and malformed JSON still fails validation (single attempt here)
    bad = answer(["chunk:csf2.0:subcategory:FAKE-99"])
    rej = GroundedGenerator(mistral(lambda r: httpx.Response(200, json=chat(json.dumps(bad)))), Settings(max_llm_attempts=1)).generate(bundle, store)
    assert rej.status != ANSWERED and rej.answer is None
    junk = GroundedGenerator(mistral(lambda r: httpx.Response(200, json=chat("not json"))), Settings(max_llm_attempts=1)).generate(bundle, store)
    assert junk.status != ANSWERED and junk.answer is None


def test_fastapi_ask_and_health_with_mistral_provider(real_db, search):
    good = answer([GV_SC_03])
    provider = mistral(lambda r: httpx.Response(200, json=chat(json.dumps(good))))
    s = Settings(db_path=real_db[0], llm_provider="mistral", mistral_api_key=SECRET, mistral_model="mistral-small-latest")
    with TestClient(create_app(lambda: Services(real_db[0], s, search, "bm25", provider, [])),
                    raise_server_exceptions=False) as client:
        health = client.get("/health")
        assert health.json()["llm"] == {"configured": True, "provider": "mistral", "model": "mistral-small-latest"}
        assert SECRET not in health.text
        r = client.post("/ask", json={"question": "What does GV.SC-03 require?"})
        assert r.status_code == 200 and SECRET not in r.text
        body = r.json()
        assert body["status"] == ANSWERED and body["answer"]["citations"] == [GV_SC_03]
        assert body["provider"] == {"name": "mistral", "model": "mistral-small-latest"}
