"""Live Gemini smoke test. Runs only when explicitly requested AND configured:

    RUN_LIVE_LLM_TESTS=1 GEMINI_API_KEY=... GEMINI_MODEL=... pytest tests/test_live_provider.py
"""
import os

import pytest

from controlshift.evidence.assemble import EvidenceAssembler
from controlshift.generation.config import Settings
from controlshift.generation.generate import ANSWERED, GroundedGenerator
from controlshift.generation.provider import GeminiProvider
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.corpus import load_corpus
from controlshift.store.queries import KnowledgeStore

pytestmark = pytest.mark.live


@pytest.mark.skipif(
    not (os.environ.get("RUN_LIVE_LLM_TESTS") == "1" and os.environ.get("GEMINI_API_KEY")
         and os.environ.get("GEMINI_MODEL")),
    reason="live LLM test not requested/configured")
def test_live_gemini_grounded_answer(real_db):
    settings = Settings.from_env()
    provider = GeminiProvider.from_settings(settings)
    with KnowledgeStore(real_db[0]) as store:
        bundle = EvidenceAssembler(store, BM25Index.build(load_corpus(real_db[0])).search,
                                   "bm25").assemble("How does GV.OC-01 map to CSF 1.1?")
        result = GroundedGenerator(provider, settings).generate(bundle, store)
    print(result.status, result.rejection)
    assert result.status == ANSWERED, result.rejection
