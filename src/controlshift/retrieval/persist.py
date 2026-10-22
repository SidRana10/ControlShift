"""Index persistence and cache invalidation.

A cached index is reused only if its fingerprint matches
sha256(corpus content hash, preprocessing settings, embedding model id, format version).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from .bm25 import BM25Index
from .chunking import DEFAULT_OVERLAP, STRATEGY
from .corpus import Doc, content_hash
from .dense import DenseIndex, Embedder
from .tokenize import preprocessing_settings

FORMAT_VERSION = 2
DEFAULT_INDEX_DIR = Path("data/indexes")


class IndexStaleError(Exception):
    """The on-disk index is missing or does not match the current corpus/settings."""


def dense_config(embedder: Embedder, overlap: int = DEFAULT_OVERLAP) -> dict:
    """Embedding-passage settings that change the vectors and so must invalidate the cache."""
    return {"max_tokens": embedder.max_tokens, "overlap_sentences": overlap, "strategy": STRATEGY}


def fingerprint(docs: list[Doc], model: str | None = None, dense: dict | None = None) -> str:
    payload = {"content": content_hash(docs), "preprocessing": preprocessing_settings(),
               "model": model, "dense": dense, "format": FORMAT_VERSION}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _atomic_write(path: Path, data: str | bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data.encode() if isinstance(data, str) else data)
    os.replace(tmp, path)


def _write_docs(index_dir: Path, docs: list[Doc]) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(index_dir / "docs.jsonl",
                  "".join(json.dumps(asdict(d), ensure_ascii=False) + "\n" for d in docs))


def _read_docs(index_dir: Path) -> list[Doc]:
    path = index_dir / "docs.jsonl"
    if not path.is_file():
        raise IndexStaleError(f"no index at {index_dir} - run `build-index`")
    return [Doc(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]


def read_manifest(index_dir: Path, kind: str) -> dict | None:
    path = index_dir / kind / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def is_fresh(index_dir: Path, kind: str, docs: list[Doc], model: str | None = None,
             dense: dict | None = None) -> bool:
    m = read_manifest(index_dir, kind)
    return m is not None and m.get("fingerprint") == fingerprint(docs, model, dense)


def build_bm25(docs: list[Doc], index_dir: Path, force: bool = False) -> tuple[str, dict]:
    """Returns ('cached'|'built', manifest)."""
    if not force and is_fresh(index_dir, "bm25", docs):
        return "cached", read_manifest(index_dir, "bm25")  # type: ignore[return-value]
    index = BM25Index.build(docs)
    out = index_dir / "bm25"
    out.mkdir(parents=True, exist_ok=True)
    _write_docs(index_dir, docs)
    _atomic_write(out / "tokens.json", json.dumps(index.tokens))
    manifest = {"kind": "bm25", "fingerprint": fingerprint(docs), "content_hash": content_hash(docs),
                "n_docs": len(docs), "preprocessing": preprocessing_settings(),
                "format": FORMAT_VERSION}
    _atomic_write(out / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True))  # last
    return "built", manifest


def build_dense(docs: list[Doc], index_dir: Path, embedder: Embedder, force: bool = False,
                overlap: int = DEFAULT_OVERLAP) -> tuple[str, dict]:
    cfg = dense_config(embedder, overlap)
    if not force and is_fresh(index_dir, "dense", docs, embedder.name, cfg):
        return "cached", read_manifest(index_dir, "dense")  # type: ignore[return-value]
    import faiss

    index = DenseIndex.build(docs, embedder, overlap)
    out = index_dir / "dense"
    out.mkdir(parents=True, exist_ok=True)
    _write_docs(index_dir, docs)
    faiss.write_index(index.index, str(out / "vectors.faiss"))
    _atomic_write(out / "passages.json", json.dumps(
        {"doc": index.passage_doc, "text": index.passage_text}, ensure_ascii=False))
    manifest = {"kind": "dense", "fingerprint": fingerprint(docs, embedder.name, cfg),
                "content_hash": content_hash(docs), "model": embedder.name, "n_docs": len(docs),
                "n_passages": len(index.passage_doc), "dim": int(index.index.d), "dense": cfg,
                "preprocessing": preprocessing_settings(), "format": FORMAT_VERSION}
    _atomic_write(out / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True))  # last
    return "built", manifest


def load_bm25(index_dir: Path, current_docs: list[Doc] | None = None) -> BM25Index:
    manifest = read_manifest(index_dir, "bm25")
    if manifest is None:
        raise IndexStaleError("BM25 index not built - run `build-index --mode bm25`")
    docs = _read_docs(index_dir)
    if current_docs is not None and manifest["fingerprint"] != fingerprint(current_docs):
        raise IndexStaleError("BM25 index is stale (corpus or preprocessing changed) - rebuild")
    return BM25Index(docs, json.loads((index_dir / "bm25" / "tokens.json").read_text()))


def load_dense(index_dir: Path, embedder: Embedder, current_docs: list[Doc] | None = None,
               overlap: int = DEFAULT_OVERLAP, backend: str | None = None) -> DenseIndex:
    import faiss

    manifest = read_manifest(index_dir, "dense")
    if manifest is None:
        raise IndexStaleError("dense index not built - run `build-index --mode dense`")
    if manifest["model"] != embedder.name:
        raise IndexStaleError(
            f"dense index was built with {manifest['model']}, not {embedder.name} - rebuild")
    if manifest["fingerprint"] != fingerprint(
            current_docs if current_docs is not None else _read_docs(index_dir), embedder.name,
            dense_config(embedder, overlap)):
        raise IndexStaleError("dense index is stale (corpus, preprocessing or chunking "
                              "settings changed) - rebuild")
    docs = _read_docs(index_dir)
    index = faiss.read_index(str(index_dir / "dense" / "vectors.faiss"))
    passages = json.loads((index_dir / "dense" / "passages.json").read_text(encoding="utf-8"))
    if index.ntotal != len(passages["doc"]):
        raise IndexStaleError("dense index/passage count mismatch - rebuild")
    return DenseIndex(docs, index, embedder, passages["doc"], passages["text"], backend)


def dir_size_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


__all__ = ["DEFAULT_INDEX_DIR", "IndexStaleError", "build_bm25", "build_dense", "fingerprint",
           "is_fresh", "load_bm25", "load_dense"]
