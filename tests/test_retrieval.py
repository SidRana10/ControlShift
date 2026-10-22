"""Phase 3A tests: BM25 + dense (with a deterministic fake embedder, no model download)."""
import dataclasses
import itertools
import json
import sqlite3

import pytest

from controlshift.retrieval import persist
from controlshift.retrieval.bm25 import BM25Index
from controlshift.retrieval.cli import main
from controlshift.retrieval.corpus import CorpusError, load_corpus
from controlshift.retrieval.dense import DenseIndex
from controlshift.retrieval.persist import (
    IndexStaleError,
    build_bm25,
    build_dense,
    fingerprint,
    load_bm25,
    load_dense,
)
from controlshift.retrieval.tokenize import tokenize
from fakes import FakeEmbedder


@pytest.fixture(scope="module")
def docs(real_db):
    return load_corpus(real_db[0])


@pytest.fixture(scope="module")
def bm25(docs):
    return BM25Index.build(docs)


@pytest.fixture(scope="module")
def dense(docs):
    return DenseIndex.build(docs, FakeEmbedder())


# ---- corpus ---------------------------------------------------------------------------
def test_corpus_covers_all_chunks_with_enriched_control_text(docs):
    assert len(docs) == 384 and len({d.chunk_id for d in docs}) == 384
    d = next(d for d in docs if d.chunk_id == "csf2.0:subcategory:GV.SC-03")
    assert d.control_id == "GV.SC-03" and d.element_id == "GV.SC-03"
    assert "Govern" in d.index_text and "Cybersecurity Supply Chain Risk Management" in d.index_text
    assert d.text.startswith("GV.SC-03:")  # shown text stays the original chunk text
    text_chunk = next(d for d in docs if d.chunk_type == "text")
    assert text_chunk.control_id is None and text_chunk.section in text_chunk.index_text


def test_corpus_missing_db(tmp_path):
    with pytest.raises(CorpusError):
        load_corpus(tmp_path / "nope.db")


# ---- tokenizer / identifier normalisation ----------------------------------------------
def test_id_normalisation_in_tokenizer():
    assert tokenize("PR.AT-1") == tokenize("pr.at-01") == ["pr.at", "pr.at-01"]
    assert "gv.sc-03" in tokenize("see GV.SC-03 now")
    assert "ex.am" not in tokenize("ex.am-1")  # unknown function prefix is not an ID
    assert tokenize("policies and the Policy") == ["policy", "policy"]


def test_exact_id_lookup_bm25(bm25):
    assert bm25.search("GV.SC-03", 1)[0].chunk_id == "csf2.0:subcategory:GV.SC-03"
    a = bm25.search("PR.AT-1", 3, "1.1")
    b = bm25.search("pr.at-01", 3, "1.1")
    assert a[0].chunk_id == "csf1.1:subcategory:PR.AT-1"
    assert [h.chunk_id for h in a] == [h.chunk_id for h in b]
    # un-padded 1.1 spelling also finds the 2.0 control that normalises to the same ID
    assert {"1.1", "2.0"} <= {h.version for h in bm25.search("PR.AT-1", 5)}


# ---- BM25 ranking ------------------------------------------------------------------------
def test_bm25_ranking_is_sorted_and_relevant(bm25):
    hits = bm25.search("data at rest is protected", 5, "1.1")
    assert hits[0].chunk_id == "csf1.1:subcategory:PR.DS-1"
    assert [h.rank for h in hits] == [1, 2, 3, 4, 5]
    assert all(a.score >= b.score for a, b in itertools.pairwise(hits))
    assert bm25.search("data at rest is protected", 5, "1.1") == hits  # deterministic


# ---- filtering / empty results -------------------------------------------------------------
@pytest.mark.parametrize("version", ["1.1", "2.0"])
def test_bm25_version_filter(bm25, version):
    hits = bm25.search("supply chain risk management", 8, version)
    assert len(hits) == 8 and {h.version for h in hits} == {version}


def test_bm25_filter_changes_statistics_not_just_post_filter(bm25, docs):
    only_11 = [d for d in docs if d.version == "1.1"]
    expected = BM25Index.build(only_11).search("incident response", 5)
    got = bm25.search("incident response", 5, "1.1")
    assert [h.chunk_id for h in got] == [h.chunk_id for h in expected]
    assert [round(h.score, 6) for h in got] == [round(h.score, 6) for h in expected]


@pytest.mark.parametrize("query", ["", "   ", "zzzzqqq xyzzy", "the of and"])
def test_empty_results(bm25, dense, query):
    assert bm25.search(query) == []
    if not query.strip():
        assert dense.search(query) == []


def test_unknown_version_returns_nothing(bm25, dense):
    assert bm25.search("risk", 5, "9.9") == [] and dense.search("risk", 5, "9.9") == []


# ---- metadata -------------------------------------------------------------------------------
def test_metadata_preserved(bm25, dense, real_db):
    conn = sqlite3.connect(real_db[0])
    for index in (bm25, dense):
        for h in index.search("asset inventory", 5):
            row = conn.execute("SELECT version, source_file, page, section, text, chunk_type "
                               "FROM chunk WHERE chunk_id=?", (h.chunk_id,)).fetchone()
            assert (h.version, h.source_file, h.page, h.section, h.text, h.chunk_type) == row
            assert isinstance(h.score, float) and h.mode in ("bm25", "dense")
            if h.chunk_type != "text":
                assert h.control_id


# ---- dense (fake embedder) ---------------------------------------------------------------------
def test_dense_self_retrieval_and_scores(dense, docs):
    d = next(d for d in docs if d.chunk_id == "csf1.1:subcategory:PR.DS-1")
    hits = dense.search(d.index_text, 3)
    assert hits[0].chunk_id == d.chunk_id and hits[0].score == pytest.approx(1.0, abs=1e-4)
    assert all(a.score >= b.score for a, b in itertools.pairwise(hits))


def test_dense_filters_before_ranking(dense, docs):
    d = next(d for d in docs if d.chunk_id == "csf1.1:subcategory:PR.DS-1")
    hits = dense.search(d.index_text, 5, "2.0")
    assert len(hits) == 5 and {h.version for h in hits} == {"2.0"}  # still a full top-5
    assert dense.search("risk", 5, "1.1")[0].version == "1.1"


# ---- persistence ----------------------------------------------------------------------------------
def test_index_persistence_roundtrip(docs, tmp_path):
    status, _ = build_bm25(docs, tmp_path)
    assert status == "built"
    status, manifest = build_dense(docs, tmp_path, FakeEmbedder())
    assert status == "built" and manifest["dim"] == 256 and manifest["n_docs"] == 384
    for rel in ("docs.jsonl", "bm25/tokens.json", "bm25/manifest.json", "dense/vectors.faiss",
                "dense/manifest.json"):
        assert (tmp_path / rel).is_file()
    fresh_b, fresh_d = load_bm25(tmp_path, docs), load_dense(tmp_path, FakeEmbedder(), docs)
    q = "least privilege access permissions"
    assert [h.chunk_id for h in fresh_b.search(q)] == [h.chunk_id for h in BM25Index.build(docs).search(q)]
    assert [h.to_dict() for h in fresh_d.search(q, 5, "2.0")] == [
        h.to_dict() for h in DenseIndex.build(docs, FakeEmbedder()).search(q, 5, "2.0")]


def test_load_without_index_raises(tmp_path):
    with pytest.raises(IndexStaleError):
        load_bm25(tmp_path)
    with pytest.raises(IndexStaleError):
        load_dense(tmp_path, FakeEmbedder())


# ---- cache invalidation ------------------------------------------------------------------------------
def test_cache_reused_when_unchanged_and_force_rebuilds(docs, tmp_path):
    assert build_bm25(docs, tmp_path)[0] == "built"
    assert build_bm25(docs, tmp_path)[0] == "cached"
    assert build_bm25(docs, tmp_path, force=True)[0] == "built"
    assert build_dense(docs, tmp_path, FakeEmbedder())[0] == "built"
    assert build_dense(docs, tmp_path, FakeEmbedder())[0] == "cached"


def test_cache_invalidated_by_content_change(docs, tmp_path):
    build_bm25(docs, tmp_path)
    build_dense(docs, tmp_path, FakeEmbedder())
    changed = [dataclasses.replace(docs[0], index_text=docs[0].index_text + " amended"), *docs[1:]]
    assert build_bm25(changed, tmp_path)[0] == "built"
    assert build_dense(changed, tmp_path, FakeEmbedder())[0] == "built"
    with pytest.raises(IndexStaleError, match="stale"):
        load_bm25(tmp_path, docs)  # index now reflects `changed`, not `docs`
    with pytest.raises(IndexStaleError, match="stale"):
        load_dense(tmp_path, FakeEmbedder(), docs)


def test_cache_invalidated_by_model_change(docs, tmp_path):
    build_dense(docs, tmp_path, FakeEmbedder("model-a"))
    assert build_dense(docs, tmp_path, FakeEmbedder("model-b"))[0] == "built"
    with pytest.raises(IndexStaleError, match="model-b"):
        load_dense(tmp_path, FakeEmbedder("model-a"), docs)
    assert fingerprint(docs, "model-a") != fingerprint(docs, "model-b")


def test_cache_invalidated_by_preprocessing_change(docs, tmp_path, monkeypatch):
    before = fingerprint(docs)
    build_bm25(docs, tmp_path)
    monkeypatch.setattr("controlshift.retrieval.tokenize.STOPWORDS", frozenset({"the"}))
    assert fingerprint(docs) != before
    assert build_bm25(docs, tmp_path)[0] == "built"


def test_manifest_written_last_so_partial_build_is_not_trusted(docs, tmp_path):
    build_bm25(docs, tmp_path)
    (tmp_path / "bm25" / "manifest.json").unlink()
    assert build_bm25(docs, tmp_path)[0] == "built"


# ---- CLI ---------------------------------------------------------------------------------------------------
def test_cli_build_and_search_bm25(real_db, tmp_path, capsys):
    base = ["--db", str(real_db[0]), "--index-dir", str(tmp_path)]
    assert main([*base, "build-index", "--mode", "bm25"]) == 0
    assert "bm25: built (384 docs)" in capsys.readouterr().out
    assert main([*base, "build-index", "--mode", "bm25"]) == 0
    assert "bm25: cached" in capsys.readouterr().out
    assert main([*base, "search", "GV.SC-03", "--mode", "bm25", "--json", "-k", "2"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits[0]["chunk_id"] == "csf2.0:subcategory:GV.SC-03" and len(hits) == 2
    assert main([*base, "search", "risk", "--mode", "bm25", "--version", "1.1", "--json"]) == 0
    assert {h["version"] for h in json.loads(capsys.readouterr().out)} == {"1.1"}
    assert main([*base, "search", "zzzzqqq", "--mode", "bm25"]) == 0
    assert "(no results)" in capsys.readouterr().out


def test_cli_errors_without_index_or_db(real_db, tmp_path, capsys):
    assert main(["--db", str(real_db[0]), "--index-dir", str(tmp_path / "none"),
                 "search", "x", "--mode", "bm25"]) == 2
    assert main(["--db", str(tmp_path / "missing.db"), "build-index", "--mode", "bm25"]) == 2


def test_persist_module_exports():
    assert persist.FORMAT_VERSION >= 1
