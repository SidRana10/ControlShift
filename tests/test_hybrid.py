"""Phase 3B tests: RRF, reranking, long-chunk passages, FAISS filtering, persistence."""
import random
import sqlite3
import sys
import types

import numpy as np
import pytest

from controlshift.retrieval import reranker as reranker_mod
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.chunking import make_passages
from controlshift.retrieval.corpus import load_corpus
from controlshift.retrieval.dense import DenseIndex
from controlshift.retrieval.fusion import rrf_fuse
from controlshift.retrieval.hits import Hit
from controlshift.retrieval.hybrid import HybridConfig, HybridRetriever
from controlshift.retrieval.persist import IndexStaleError, build_dense, load_dense
from controlshift.retrieval.reranker import CrossEncoderScorer, rerank
from fakes import FakeEmbedder, KeywordScorer


def hit(cid, rank, score=1.0, mode="bm25", version="2.0"):
    return Hit(rank=rank, score=score, mode=mode, chunk_id=cid, version=version, control_id=cid,
               chunk_type="subcategory", source_file="f.pdf", page=3, printed_page="2",
               section="S", text=f"text {cid}")


@pytest.fixture(scope="module")
def docs(real_db):
    return load_corpus(real_db[0])


@pytest.fixture(scope="module")
def retriever(docs):
    return HybridRetriever(BM25Index.build(docs), DenseIndex.build(docs, FakeEmbedder()),
                           KeywordScorer(["supplier"]))


# ---- RRF ---------------------------------------------------------------------------------
def test_rrf_scores_are_exact():
    fused = rrf_fuse({"bm25": [hit("a", 1), hit("b", 2), hit("c", 3)],
                      "dense": [hit("b", 1), hit("d", 2)]}, k=60)
    scores = {h.chunk_id: h.score for h in fused}
    assert scores["a"] == pytest.approx(1 / 61)
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["c"] == pytest.approx(1 / 63)
    assert scores["d"] == pytest.approx(1 / 62)
    assert [h.chunk_id for h in fused] == ["b", "a", "d", "c"]
    assert [h.rank for h in fused] == [1, 2, 3, 4] and all(h.mode == "hybrid" for h in fused)


def test_rrf_k_is_configurable():
    fused = rrf_fuse({"x": [hit("a", 1)]}, k=10)
    assert fused[0].score == pytest.approx(1 / 11)
    with pytest.raises(ValueError):
        rrf_fuse({"x": [hit("a", 1)]}, k=-1)


def test_rrf_uses_ranks_not_scores():
    lo = rrf_fuse({"bm25": [hit("a", 1, 0.001), hit("b", 2, 0.0009)],
                   "dense": [hit("b", 1, 99.0), hit("a", 2, 98.0)]})
    hi = rrf_fuse({"bm25": [hit("a", 1, 9000.0), hit("b", 2, 1.0)],
                   "dense": [hit("b", 1, 0.5), hit("a", 2, 0.4)]})
    assert [(h.chunk_id, h.score) for h in lo] == [(h.chunk_id, h.score) for h in hi]


def test_duplicates_merge_and_keep_metadata_and_components():
    fused = rrf_fuse({"bm25": [hit("a", 1, 7.5), hit("a", 2, 7.4)],  # repeated id in one list
                      "dense": [hit("a", 1, 0.8)]})
    assert len(fused) == 1
    h = fused[0]
    assert h.score == pytest.approx(2 / 61)  # repeat inside a list is ignored
    assert (h.source_file, h.page, h.section, h.version) == ("f.pdf", 3, "S", "2.0")
    assert h.components["bm25"] == {"rank": 1, "score": 7.5}
    assert h.components["dense"] == {"rank": 1, "score": 0.8}
    assert h.components["rrf"]["rank"] == 1


def test_rrf_tie_break_is_deterministic():
    # b and c tie on score; best rank equal -> chunk_id decides. d has worse best rank.
    lists = {"one": [hit("c", 1), hit("d", 2)], "two": [hit("b", 1), hit("d", 2)]}
    expected = ["d", "b", "c"]  # d: 1/62+1/62 beats the 1/61 singles
    for seed in range(5):
        keys = list(lists)
        random.Random(seed).shuffle(keys)
        assert [h.chunk_id for h in rrf_fuse({k: lists[k] for k in keys})] == expected
    tie = rrf_fuse({"one": [hit("z", 1)], "two": [hit("a", 1)]})
    assert [h.chunk_id for h in tie] == ["a", "z"]


def test_rrf_empty():
    assert rrf_fuse({}) == [] and rrf_fuse({"bm25": [], "dense": []}) == []


# ---- hybrid pipeline -----------------------------------------------------------------------------
def test_hybrid_exact_id_and_candidate_pool(retriever):
    hits = retriever.search("GV.SC-03", 5)
    assert "csf2.0:subcategory:GV.SC-03" in [h.chunk_id for h in hits[:2]]
    assert len({h.chunk_id for h in hits}) == len(hits)
    assert set(hits[0].components) >= {"rrf"}
    pool_small = HybridRetriever(retriever.bm25, retriever.dense, config=HybridConfig(pool=2))
    assert len(pool_small.fuse("supplier risk")) <= 4  # at most 2 per retriever


@pytest.mark.parametrize("version", ["1.1", "2.0"])
def test_hybrid_version_filter(retriever, version):
    hits = retriever.search("incident response and recovery", 10, version)
    assert len(hits) == 10 and {h.version for h in hits} == {version}
    reranked = retriever.search("supplier", 5, version, rerank_results=True)
    assert {h.version for h in reranked} == {version}


def test_hybrid_empty_results(retriever):
    assert retriever.search("   ", 5) == []
    assert retriever.search("risk", 5, "9.9") == []
    assert retriever.search("risk", 5, "9.9", rerank_results=True) == []


def test_hybrid_is_stable_across_calls(retriever):
    a = retriever.search("access control for remote users", 8)
    b = retriever.search("access control for remote users", 8)
    assert [h.to_dict() for h in a] == [h.to_dict() for h in b]


def test_hybrid_preserves_citation_metadata(retriever, real_db):
    conn = sqlite3.connect(real_db[0])
    for rr in (False, True):
        for h in retriever.search("asset inventory", 5, rerank_results=rr):
            row = conn.execute("SELECT version, source_file, page, printed_page, section, text "
                               "FROM chunk WHERE chunk_id=?", (h.chunk_id,)).fetchone()
            assert (h.version, h.source_file, h.page, h.printed_page, h.section, h.text) == row


# ---- reranking ------------------------------------------------------------------------------------------
def test_rerank_orders_by_cross_encoder_and_keeps_original_ranks():
    hits = [hit("a", 1, 0.9, "hybrid"), hit("b", 2, 0.8, "hybrid"), hit("c", 3, 0.7, "hybrid")]
    passages = {"a": "nothing", "b": "supplier supplier", "c": "supplier"}

    class Scorer:
        name = "s"

        def score(self, query, texts):
            return [float(t.count("supplier")) for t in texts]

    out = rerank("q", hits, passages, Scorer())
    assert [h.chunk_id for h in out] == ["b", "c", "a"] and [h.rank for h in out] == [1, 2, 3]
    assert [h.score for h in out] == [2.0, 1.0, 0.0] and all(h.mode == "hybrid_rerank" for h in out)
    assert out[0].components["hybrid"] == {"rank": 2, "score": 0.8}  # prior stage preserved
    assert out[0].components["rerank"] == {"rank": 1, "score": 2.0}
    assert [h.chunk_id for h in rerank("q", hits, passages, Scorer(), top_k=2)] == ["b", "c"]


def test_rerank_ties_fall_back_to_incoming_rank_then_id():
    hits = [hit("z", 1, mode="hybrid"), hit("y", 2, mode="hybrid")]

    class Flat:
        name = "flat"

        def score(self, q, texts):
            return [0.5] * len(texts)

    assert [h.chunk_id for h in rerank("q", hits, {"z": "", "y": ""}, Flat())] == ["z", "y"]


def test_rerank_empty_inputs():
    assert rerank("q", [], {}, KeywordScorer(["x"])) == []
    assert rerank("  ", [hit("a", 1)], {"a": "t"}, KeywordScorer(["x"])) == []


def test_pipeline_rerank_uses_scorer_and_requires_one(retriever, docs):
    out = retriever.search("supplier risk", 5, rerank_results=True)
    assert out and all(h.mode == "hybrid_rerank" for h in out)
    assert out[0].score >= out[-1].score
    assert {"rrf", "rerank"} <= set(out[0].components)
    no_scorer = HybridRetriever(retriever.bm25, retriever.dense)
    with pytest.raises(ValueError, match="reranker"):
        no_scorer.search("x", 5, rerank_results=True)


def test_reranker_model_is_cached_per_process(monkeypatch):
    loads = []

    class FakeCE:
        def __init__(self, name, max_length):
            loads.append(name)

        tokenizer = staticmethod(lambda text, add_special_tokens=False: {"input_ids": text.split()})

        def predict(self, pairs, **kw):
            return np.arange(len(pairs), dtype=float)

    # A stub module avoids importing torch after FAISS has run in-process (OpenMP abort on macOS).
    stub = types.ModuleType("sentence_transformers")
    stub.CrossEncoder = FakeCE
    monkeypatch.setitem(sys.modules, "sentence_transformers", stub)
    monkeypatch.setattr(reranker_mod, "_MODELS", {})
    a, b = CrossEncoderScorer("m"), CrossEncoderScorer("m")
    assert a.score("q", ["x", "y"]) == [0.0, 1.0] and b.score("q", ["z"]) == [0.0]
    assert loads == ["m"]
    assert a.score("q", []) == []


# ---- long chunks ---------------------------------------------------------------------------------------------
def test_real_corpus_has_over_long_chunks_for_small_limit(docs):
    emb = FakeEmbedder(max_tokens=60)
    assert sum(len(make_passages(d, emb)) > 1 for d in docs) > 10


def test_passages_respect_limit_cover_all_content_and_keep_prefix(docs):
    emb = FakeEmbedder(max_tokens=60)
    for d in (d for d in docs if emb.count_tokens(d.index_text) > 60):
        passages = make_passages(d, emb)
        assert len(passages) > 1
        assert all(emb.count_tokens(p) <= 60 for p in passages)
        assert all(p.startswith(d.index_prefix) for p in passages)
        joined = " ".join(p[len(d.index_prefix):] for p in passages)
        for word in d.index_text[len(d.index_prefix):].split():
            assert word in joined  # nothing silently dropped
        assert d.text  # original text untouched for citation


def test_short_docs_are_single_unchanged_passages(docs):
    emb = FakeEmbedder()
    assert all(make_passages(d, emb) == [d.index_text] for d in docs[:20])


def test_long_chunk_found_via_late_passage_and_cites_parent(docs):
    emb = FakeEmbedder(max_tokens=60)
    index = DenseIndex.build(docs, emb)
    assert index.index.ntotal > len(docs)
    long_doc = max(docs, key=lambda d: len(d.index_text))
    tail_sentence = long_doc.index_text.split(". ")[-1]
    hits = index.search(tail_sentence, 3)
    top = next(h for h in hits if h.chunk_id == long_doc.chunk_id)
    assert top.rank <= 3 and top.matched_passage and tail_sentence[:30] in top.matched_passage
    assert (top.page, top.section, top.source_file, top.text) == (
        long_doc.page, long_doc.section, long_doc.source_file, long_doc.text)
    assert len({h.chunk_id for h in hits}) == len(hits)  # one hit per parent chunk


# ---- FAISS filtering correctness ---------------------------------------------------------------------------------
def brute_force(index, query, k, version):
    qv = index.embedder.encode([query])[0]
    vecs = index.index.reconstruct_n(0, index.index.ntotal)
    best = {}
    for p, doc_i in enumerate(index.passage_doc):
        if version and index.docs[doc_i].version != version:
            continue
        s = float(vecs[p] @ qv)
        if doc_i not in best or s > best[doc_i]:
            best[doc_i] = s
    ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return [index.docs[i].chunk_id for i, _ in ranked]


@pytest.mark.parametrize("query", ["supplier risk", "GV.SC-03", "encrypt data at rest",
                                   "recovery communications", "asset inventory devices"])
@pytest.mark.parametrize("version", [None, "1.1", "2.0"])
@pytest.mark.parametrize("backend", ["faiss", "numpy"])
def test_filter_matches_exhaustive_search_within_version(docs, query, version, backend):
    index = DenseIndex.build(docs, FakeEmbedder(max_tokens=60), backend=backend)
    got = [h.chunk_id for h in index.search(query, 10, version)]
    assert got == brute_force(index, query, 10, version)
    if version:
        assert all(c.startswith(f"csf{version}:") for c in got) and len(got) == 10


# ---- persistence / invalidation ---------------------------------------------------------------------------------------
def test_dense_persistence_with_passages(docs, tmp_path):
    emb = FakeEmbedder(max_tokens=60)
    status, manifest = build_dense(docs, tmp_path, emb)
    assert status == "built" and manifest["n_passages"] > manifest["n_docs"] == 384
    loaded = load_dense(tmp_path, emb, docs)
    fresh = DenseIndex.build(docs, emb)
    q = "supplier risk"
    assert [h.to_dict() for h in loaded.search(q, 5, "2.0")] == [
        h.to_dict() for h in fresh.search(q, 5, "2.0")]


def test_chunking_config_changes_invalidate_cache(docs, tmp_path):
    build_dense(docs, tmp_path, FakeEmbedder(max_tokens=60))
    assert build_dense(docs, tmp_path, FakeEmbedder(max_tokens=60))[0] == "cached"
    assert build_dense(docs, tmp_path, FakeEmbedder(max_tokens=80))[0] == "built"
    assert build_dense(docs, tmp_path, FakeEmbedder(max_tokens=80), overlap=0)[0] == "built"
    with pytest.raises(IndexStaleError, match="stale"):
        load_dense(tmp_path, FakeEmbedder(max_tokens=60), docs)
    with pytest.raises(IndexStaleError):
        load_dense(tmp_path, FakeEmbedder(max_tokens=80), docs)  # built with overlap=0 last


def test_backends_return_identical_results(docs):
    emb = FakeEmbedder(max_tokens=60)
    a, b = (DenseIndex.build(docs, emb, backend=x) for x in ("faiss", "numpy"))
    for q in ("supplier risk", "GV.SC-03", "recovery plan communications"):
        for v in (None, "1.1", "2.0"):
            ha, hb = a.search(q, 8, v), b.search(q, 8, v)
            assert [h.chunk_id for h in ha] == [h.chunk_id for h in hb]
            assert [h.score for h in ha] == pytest.approx([h.score for h in hb], abs=1e-5)


def test_backend_resolution(monkeypatch):
    from controlshift.retrieval.dense import resolve_backend

    monkeypatch.delenv("CONTROLSHIFT_DENSE_BACKEND", raising=False)
    assert resolve_backend("faiss") == "faiss" and resolve_backend("numpy") == "numpy"
    monkeypatch.setattr(sys, "platform", "darwin")
    assert resolve_backend() == "numpy"
    monkeypatch.setattr(sys, "platform", "linux")
    assert resolve_backend("auto") == "faiss"
    monkeypatch.setenv("CONTROLSHIFT_DENSE_BACKEND", "numpy")
    assert resolve_backend() == "numpy"
    with pytest.raises(ValueError):
        resolve_backend("annoy")


def test_split_to_fit_never_drops_content():
    from controlshift.retrieval.reranker import split_to_fit

    count = lambda t: len(t.split())
    text = "One two three. Four five six seven. Eight nine ten eleven twelve thirteen."
    assert split_to_fit(text, 50, count) == [text]
    windows = split_to_fit(text, 7, count)
    assert len(windows) > 1 and all(count(w) <= 7 for w in windows)
    assert " ".join(windows).split() == text.split()
    giant = "w " * 40  # a single sentence longer than the budget is word-windowed
    assert " ".join(split_to_fit(giant, 10, count)).split() == giant.split()


def test_cross_encoder_scores_overlong_passage_by_best_window(monkeypatch):
    seen = []

    class FakeCE:
        tokenizer = staticmethod(lambda text, add_special_tokens=False: {"input_ids": text.split()})

        def __init__(self, name, max_length):
            pass

        def predict(self, pairs, **kw):
            seen.extend(pairs)
            return [10.0 if "needle" in p else 1.0 for _, p in pairs]

    stub = types.ModuleType("sentence_transformers")
    stub.CrossEncoder = FakeCE
    monkeypatch.setitem(sys.modules, "sentence_transformers", stub)
    monkeypatch.setattr(reranker_mod, "_MODELS", {})
    scorer = CrossEncoderScorer("m", max_length=30)
    long_passage = ". ".join([*(f"filler sentence number {i}" for i in range(12)),
                              "the needle is here"]) + "."
    short, long_ = scorer.score("query words", ["tiny text", long_passage])
    assert short == 1.0 and long_ == 10.0  # the late 'needle' sentence was not truncated away
    assert scorer.windowed == 1 and all(len(p.split()) <= 30 - 2 - 3 for _, p in seen)


def test_unsafe_faiss_backend_refused_on_macos_but_not_elsewhere(monkeypatch, docs):
    from controlshift.retrieval.dense import ALLOW_UNSAFE_ENV, UnsafeBackendError, resolve_backend

    monkeypatch.delenv("CONTROLSHIFT_DENSE_BACKEND", raising=False)
    monkeypatch.delenv(ALLOW_UNSAFE_ENV, raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(UnsafeBackendError, match="--dense-backend numpy"):
        resolve_backend("faiss")
    monkeypatch.setenv("CONTROLSHIFT_DENSE_BACKEND", "faiss")  # same refusal via the env var
    with pytest.raises(UnsafeBackendError):
        resolve_backend()
    with pytest.raises(UnsafeBackendError):  # and when constructing an index directly
        DenseIndex.build(docs[:5], FakeEmbedder(), backend="faiss")
    monkeypatch.delenv("CONTROLSHIFT_DENSE_BACKEND")
    assert resolve_backend("auto") == resolve_backend("numpy") == "numpy"
    monkeypatch.setenv(ALLOW_UNSAFE_ENV, "1")  # explicit diagnostic override
    assert resolve_backend("faiss") == "faiss"
    monkeypatch.delenv(ALLOW_UNSAFE_ENV)
    monkeypatch.setattr(sys, "platform", "linux")
    assert resolve_backend("faiss") == "faiss"
