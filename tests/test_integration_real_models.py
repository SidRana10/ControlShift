"""Integration tests with the real MiniLM embedder and cross-encoder.

They run in subprocesses (importing torch after FAISS has run in-process aborts on macOS) and
are skipped when the models are not in the local Hugging Face cache - nothing is downloaded.
"""
import json
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.integration

MODELS = ["sentence-transformers/all-MiniLM-L6-v2", "cross-encoder/ms-marco-MiniLM-L-6-v2"]


def _cached(model):
    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return False
    return isinstance(try_to_load_from_cache(model, "config.json"), str)


@pytest.fixture(scope="module")
def built(real_db, tmp_path_factory):
    if not all(_cached(m) for m in MODELS):
        pytest.skip("real models not in local HF cache")
    index_dir = tmp_path_factory.mktemp("real_index")
    base = [sys.executable, "-m", "controlshift.retrieval.cli", "--db", str(real_db[0]),
            "--index-dir", str(index_dir)]
    out = subprocess.run([*base, "build-index"], capture_output=True, text=True, check=True)
    assert "dense: built" in out.stdout
    return base, index_dir


def search(base, query, mode, *extra):
    out = subprocess.run([*base, "search", query, "--mode", mode, "--json", *extra],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_real_index_splits_over_long_chunks(built):
    _, index_dir = built
    manifest = json.loads((index_dir / "dense" / "manifest.json").read_text())
    assert manifest["n_docs"] == 384 and manifest["n_passages"] > 384
    code = (
        "import json,sys;from sentence_transformers import SentenceTransformer as S;"
        "m=S('sentence-transformers/all-MiniLM-L6-v2');"
        "p=json.load(open(sys.argv[1]))['text'];"
        "print(max(len(m.tokenizer(t)['input_ids']) for t in p))")
    out = subprocess.run([sys.executable, "-c", code, str(index_dir / "dense" / "passages.json")],
                         capture_output=True, text=True, check=True)
    assert int(out.stdout.strip().splitlines()[-1]) <= 256  # every embedded passage fits


def test_real_hybrid_and_rerank_modes(built):
    base, _ = built
    for mode in ("bm25", "dense", "hybrid", "hybrid_rerank"):
        hits = search(base, "GV.SC-03", mode, "-k", "5")
        assert len(hits) == 5 and all(h["mode"] == mode for h in hits)
        ids = [h["chunk_id"] for h in hits]
        if mode == "bm25":
            assert ids[0] == "csf2.0:subcategory:GV.SC-03"
        elif mode != "dense":  # dense alone ranks bare IDs weakly (documented limitation); an
            # equal-weight RRF tie between bm25#1/dense#3 and bm25#3/dense#1 is possible
            assert "csf2.0:subcategory:GV.SC-03" in ids[:2]
    supplier = search(base, "How should organizations manage supplier risks?", "hybrid_rerank")
    assert len(supplier) == 5  # relevance is judged in the Phase 5 benchmark, not here
    scores = [h["score"] for h in supplier]
    assert scores == sorted(scores, reverse=True)
    assert "rerank" in supplier[0]["components"] and "rrf" in supplier[0]["components"]


def test_real_version_filter_returns_full_topk(built):
    base, _ = built
    for mode in ("bm25", "dense", "hybrid", "hybrid_rerank"):
        hits = search(base, "How should sensitive information be protected at rest?", mode,
                      "--version", "1.1", "-k", "5")
        assert len(hits) == 5 and {h["version"] for h in hits} == {"1.1"}


SEQUENCE = """
    import sys, tempfile
    from pathlib import Path
    from controlshift.retrieval.bm25 import BM25Index
    from controlshift.retrieval.corpus import load_corpus
    from controlshift.retrieval.dense import SentenceTransformerEmbedder
    from controlshift.retrieval.hybrid import HybridRetriever
    from controlshift.retrieval.persist import build_dense, load_dense
    from controlshift.retrieval.reranker import CrossEncoderScorer

    docs = load_corpus(sys.argv[1])
    emb, scorer = SentenceTransformerEmbedder(), CrossEncoderScorer()
    queries = ["GV.SC-03", "How should organizations manage supplier risks?",
               "How should sensitive information be protected at rest?",
               "recovery communications to stakeholders", "asset inventory", "least privilege"]
    with tempfile.TemporaryDirectory() as d:
        build_dense(docs, Path(d), emb)                        # heavy torch encode + faiss add/write
        dense = load_dense(Path(d), emb, docs)                 # faiss read + reconstruct
        r = HybridRetriever(BM25Index.build(docs), dense, scorer)
        for rnd in range(2):                                   # search / encode / rerank interleaved
            for q in queries:
                for v in (None, "1.1", "2.0"):
                    for rr in (False, True):
                        assert len(r.search(q, 5, v, rerank_results=rr)) == 5
                emb.encode([f"batch {i} {q}" for i in range(64)])   # large torch batch after a search
        # no (query, passage) pair is truncated: score every document for each query
        for q in queries + ["very long query " * 20]:
            scorer.score(q, [x.index_text for x in docs])
        print("backend", dense.backend, "windowed", scorer.windowed, "SEQUENCE OK")
"""


def test_real_models_survive_interleaved_encode_search_and_rerank_in_one_process(built, real_db):
    out = subprocess.run([sys.executable, "-W", "ignore", "-c", textwrap.dedent(SEQUENCE),
                          str(real_db[0])], capture_output=True, text=True, check=False)
    assert out.returncode == 0, out.stderr[-1000:]
    assert "SEQUENCE OK" in out.stdout
    assert "windowed 0 " in out.stdout, out.stdout  # nothing needed windowing: no truncation


def test_real_cli_dense_backend_choices_agree(built):
    base, _ = built
    q = "supplier risk management"
    auto = search(base, q, "dense", "--version", "2.0")
    numpy_ = search(base, q, "dense", "--version", "2.0", "--dense-backend", "numpy")
    assert [h["chunk_id"] for h in auto] == [h["chunk_id"] for h in numpy_]
    # hybrid_rerank (torch + dense search + cross-encoder in one process) with the default backend
    assert len(search(base, q, "hybrid_rerank", "--dense-backend", "auto")) == 5
