"""FastAPI: validation, controlled errors, timeouts, service reuse (fake LLM, BM25 retrieval)."""
import time

import pytest
from fastapi.testclient import TestClient

from controlshift.api.app import create_app
from controlshift.api.services import Services, build_services
from controlshift.generation.config import Settings
from controlshift.generation.provider import ProviderFailure, ProviderTimeout
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from fakes import FakeProvider, answer

GV_SC_03 = "chunk:csf2.0:subcategory:GV.SC-03"


@pytest.fixture(scope="module")
def bm25_search(real_db):
    return BM25Index.build(load_corpus(real_db[0])).search


def make(real_db, search, provider, **settings):
    s = Settings(db_path=real_db[0], **settings)
    return Services(real_db[0], s, search, "bm25", provider, [])


@pytest.fixture
def client_for(real_db, bm25_search):
    created = []

    def factory(provider=None, request_timeout=None, **settings):
        calls = {"n": 0}

        def services_factory():
            calls["n"] += 1
            return make(real_db, bm25_search, provider, **settings)

        client = TestClient(create_app(services_factory, request_timeout), raise_server_exceptions=False)
        client.__enter__()
        created.append(client)
        client.factory_calls = calls
        return client

    yield factory
    for c in created:
        c.__exit__(None, None, None)


def test_health_has_no_secrets(client_for):
    client = client_for(FakeProvider(answer([GV_SC_03])), gemini_api_key="SECRET-123")
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["database"] == {"chunks": 384, "elements": 270,
                                                           "crosswalk_rows": 205}
    assert body["llm"] == {"configured": True, "provider": "fake", "model": "fake-model-1"}
    assert "SECRET-123" not in client.get("/health").text
    assert client_for(None).get("/health").json()["llm"]["configured"] is False


def test_ask_end_to_end(client_for):
    provider = FakeProvider(answer([GV_SC_03], "GV.SC-03 integrates supply chain risk management."))
    r = client_for(provider).post("/ask", json={"question": "What does GV.SC-03 require?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered" and body["answer"]["citations"] == [GV_SC_03]
    assert body["evidence"]["query_type"] == "single_version"
    assert body["evidence"]["control_records"][0]["control_id"] == "GV.SC-03"
    assert body["verification"]["semantic_faithfulness"] == "not verified"
    assert body["provider"] == {"name": "fake", "model": "fake-model-1"}
    assert len(provider.calls) == 1


def test_version_field_is_applied_and_isolates_evidence(client_for):
    provider = FakeProvider(answer(["chunk:csf1.1:subcategory:PR.DS-1"]))
    r = client_for(provider).post("/ask", json={"question": "How is data at rest protected?",
                                                "version": "1.1"})
    body = r.json()
    assert body["effective_question"].startswith("In CSF 1.1:")
    assert body["evidence"]["searched_versions"] == ["1.1"]
    assert {p["version"] for p in body["evidence"]["passages"]} == {"1.1"}


def test_compare_endpoint_covers_both_versions(client_for):
    provider = FakeProvider(answer(["xwalk:row4", "xwalk:row5"]))
    r = client_for(provider).post("/compare", json={"question": "How did it change?",
                                                    "control_ids": ["gv.oc-01"]})
    body = r.json()
    assert r.status_code == 200 and body["evidence"]["query_type"] == "control_mapping"
    assert body["effective_question"] == "Compare CSF 1.1 and CSF 2.0 for GV.OC-01: How did it change?"
    assert {c["excel_row"] for c in body["evidence"]["crosswalk_records"]} == {4, 5}
    assert set(body["evidence"]["searched_versions"]) == {"1.1", "2.0"}


def test_evidence_only_modes(client_for):
    no_llm = client_for(None).post("/ask", json={"question": "What does GV.SC-03 require?"}).json()
    assert no_llm["status"] == "evidence_only" and no_llm["answer"] is None
    assert no_llm["evidence"]["control_records"] and "GEMINI_API_KEY" in no_llm["warnings"][0]
    provider = FakeProvider(answer([GV_SC_03]))
    off = client_for(provider).post("/ask", json={"question": "What does GV.SC-03 require?",
                                                  "generate": False, "include_evidence": False}).json()
    assert off["status"] == "evidence_only" and off["evidence"] is None and provider.calls == []


def test_abstention_and_rejection_are_reported_not_hidden(client_for):
    c = client_for(FakeProvider(answer([GV_SC_03, "chunk:made:up"])))
    assert c.post("/ask", json={"question": "What does GV.SC-03 require?"}).json()["status"] == "rejected"
    abst = client_for(FakeProvider(answer([]))).post("/ask", json={"question": "zzzzqqq xyzzy"})
    assert abst.json()["status"] == "abstained" and abst.json()["answer"] is None


@pytest.mark.parametrize("payload", [
    {}, {"question": ""}, {"question": "   "}, {"question": "x" * 2001}, {"question": "ok", "version": "3.0"},
    {"question": "ok", "retrieval_k": 0}, {"question": "ok", "retrieval_k": 99}, {"question": 5},
    {"question": "ok", "unknown_field": 1}, {"question": "bad\x00char"},
])
def test_ask_input_validation(client_for, payload):
    provider = FakeProvider(answer([GV_SC_03]))
    r = client_for(provider).post("/ask", json=payload)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"
    assert r.json()["error"]["details"] and provider.calls == []


@pytest.mark.parametrize("payload", [{"question": "ok", "control_ids": ["nonsense"]},
                                     {"question": "ok", "control_ids": ["GV.SC-03"] * 6}])
def test_compare_input_validation(client_for, payload):
    assert client_for(None).post("/compare", json=payload).status_code == 422


def test_malformed_json_and_unknown_route(client_for):
    c = client_for(None)
    assert c.post("/ask", content="{not json", headers={"content-type": "application/json"}).status_code == 422
    assert c.get("/nope").status_code == 404
    assert c.get("/ask").status_code == 405


def test_provider_failures_are_mapped_to_controlled_errors(client_for):
    r = client_for(FakeProvider(ProviderFailure("Gemini returned HTTP 500"))).post(
        "/ask", json={"question": "What does GV.SC-03 require?"})
    assert r.status_code == 502 and r.json()["error"] == {
        "code": "provider_error", "message": "Gemini returned HTTP 500", "details": None}
    r = client_for(FakeProvider(ProviderTimeout("timed out after 30s"))).post(
        "/ask", json={"question": "What does GV.SC-03 require?"})
    assert r.status_code == 504 and r.json()["error"]["code"] == "provider_timeout"


def test_request_timeout_returns_504(client_for):
    def slow(system, prompt):
        time.sleep(1.0)
        return answer([GV_SC_03])

    r = client_for(FakeProvider(slow), request_timeout=0.2).post(
        "/ask", json={"question": "What does GV.SC-03 require?"})
    assert r.status_code == 504 and r.json()["error"]["code"] == "request_timeout"


def test_unexpected_errors_do_not_leak_internals(client_for):
    r = client_for(FakeProvider(RuntimeError("secret internal path /etc/passwd"))).post(
        "/ask", json={"question": "What does GV.SC-03 require?"})
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert "passwd" not in r.text


def test_services_are_built_once_and_reused_across_requests(client_for):
    provider = FakeProvider(answer([GV_SC_03]))
    c = client_for(provider)
    for _ in range(3):
        assert c.post("/ask", json={"question": "What does GV.SC-03 require?"}).status_code == 200
    c.get("/health")
    assert c.factory_calls["n"] == 1 and len(provider.calls) == 3


def test_build_services_without_models_and_without_credentials(real_db, tmp_path):
    s = Settings(db_path=real_db[0], retrieval_mode="none", index_dir=tmp_path)
    svc = build_services(s)
    assert svc.provider is None and svc.models_loaded == [] and svc.retriever is None
    assert svc.health()["llm"]["configured"] is False


def test_build_services_loads_models_once_at_startup(real_db, tmp_path, monkeypatch):
    """Warm-up forces the lazy model load during startup, so requests never pay for it."""
    import controlshift.evidence.cli as ecli

    loads = {"n": 0}

    def fake_build_retriever(mode, db, index_dir):
        loads["n"] += 1
        return (lambda q, k, v: []), mode

    monkeypatch.setattr(ecli, "build_retriever", fake_build_retriever)
    svc = build_services(Settings(db_path=real_db[0], retrieval_mode="hybrid_rerank"))
    assert loads["n"] == 1 and svc.models_loaded == ["embedder", "cross-encoder"]
