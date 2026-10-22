"""Regression tests for the macOS FAISS + torch OpenMP conflict (see retrieval/dense.py).

Root cause: faiss-cpu and torch each bundle their own libomp.dylib; once a FAISS search AND a torch
parallel op have both run in one process, the OpenMP runtime aborts ("OMP: Error #15"), whatever
the import order or thread settings. These tests run in fresh subprocesses because the failure
kills the interpreter.
"""
import importlib.util
import os
import subprocess
import sys
import textwrap

import pytest

# find_spec, not importorskip: importing torch into the pytest process would itself trigger the
# clash with the in-process FAISS searches done by other tests.
if not (importlib.util.find_spec("torch") and importlib.util.find_spec("faiss")):
    pytest.skip("torch and faiss are required", allow_module_level=True)
darwin_only = pytest.mark.skipif(sys.platform != "darwin", reason="bundled-libomp clash is macOS")


def run(code, **env):
    full_env = {k: v for k, v in os.environ.items() if k != "KMP_DUPLICATE_LIB_OK"} | env
    return subprocess.run([sys.executable, "-W", "ignore", "-c", textwrap.dedent(code)],
                          capture_output=True, text=True, env=full_env, check=False)


CONFLICT = """
    import numpy as np, faiss, torch
    ix = faiss.IndexFlatIP(32); ix.add(np.random.rand(500, 32).astype('float32'))
    ix.search(np.random.rand(1, 32).astype('float32'), 5)   # FAISS OpenMP runtime starts
    (torch.rand(256, 256) @ torch.rand(256, 256))            # torch OpenMP runtime starts
    print('NO CRASH')
"""


@darwin_only
def test_canary_faiss_search_plus_torch_op_still_aborts():
    """Documents the root cause. If this stops crashing (new wheels), the numpy default for
    macOS can be revisited - the test then skips instead of failing."""
    r = run(CONFLICT)
    if r.returncode == 0:
        pytest.skip("FAISS+torch conflict no longer reproduces with the installed wheels")
    assert "OMP: Error #15" in r.stderr


@darwin_only
@pytest.mark.parametrize("env", [{"OMP_NUM_THREADS": "1"}, {"MKL_NUM_THREADS": "1"}])
def test_limiting_threads_is_not_a_fix(env):
    r = run(CONFLICT, **env)
    if r.returncode == 0:
        pytest.skip("conflict no longer reproduces")
    assert "OMP: Error #15" in r.stderr


SUPPORTED = """
    import sys, pathlib, tempfile
    sys.path.insert(0, {tests_dir!r})
    import numpy as np, torch, faiss
    from controlshift.retrieval.corpus import Doc
    from controlshift.retrieval.dense import DenseIndex, resolve_backend

    class TorchEmbedder:                 # real torch parallel work on every encode
        name, max_tokens = 'torch-test', 256
        def count_tokens(self, t): return len(t.split())
        def encode(self, texts):
            g = torch.Generator().manual_seed(0)
            w = torch.randn(64, 128, generator=g)
            x = torch.stack([torch.tensor([hash(t) % 97 + i for i in range(64)], dtype=torch.float32)
                             for t in texts])
            y = torch.nn.functional.normalize((x @ w) @ (w.T @ w), dim=1)
            return np.ascontiguousarray(y.numpy(), dtype=np.float32)

    docs = [Doc(chunk_id=f'c{{i}}', version='1.1' if i % 2 else '2.0', chunk_type='text',
                control_id=None, element_id=None, source_file='f.pdf', page=1, printed_page='1',
                section='S', text=f'text number {{i}}', index_text=f'text number {{i}}')
            for i in range(300)]
    assert resolve_backend() == 'numpy'
    for round_ in range(3):                                   # interleave torch and search
        emb = TorchEmbedder()
        ix = DenseIndex.build(docs, emb)                      # torch encode + faiss add
        with tempfile.TemporaryDirectory() as d:
            faiss.write_index(ix.index, d + '/v.faiss')
            ix2 = DenseIndex(docs, faiss.read_index(d + '/v.faiss'), emb,
                             ix.passage_doc, ix.passage_text)
        for v in (None, '1.1', '2.0'):
            hits = ix2.search('text number 7', 5, v)
            assert len(hits) == 5 and (v is None or {{h.version for h in hits}} == {{v}})
        torch.rand(512, 512) @ torch.rand(512, 512)           # torch work after search
    print('SUPPORTED SEQUENCE OK')
"""


def test_supported_startup_sequence_survives_interleaved_torch_and_search():
    from pathlib import Path

    code = SUPPORTED.format(tests_dir=str(Path(__file__).parent))
    r = run(code)
    assert r.returncode == 0, r.stderr[-800:]
    assert "SUPPORTED SEQUENCE OK" in r.stdout


@darwin_only
def test_overridden_faiss_backend_still_aborts_with_torch():
    code = SUPPORTED.replace("assert resolve_backend() == 'numpy'", "").replace(
        "DenseIndex.build(docs, emb)", "DenseIndex.build(docs, emb, backend='faiss')").replace(
        "DenseIndex(docs, faiss.read_index(d + '/v.faiss'), emb,\n                             "
        "ix.passage_doc, ix.passage_text)",
        "DenseIndex(docs, faiss.read_index(d + '/v.faiss'), emb,\n                             "
        "ix.passage_doc, ix.passage_text, backend='faiss')")
    from pathlib import Path

    r = run(code.format(tests_dir=str(Path(__file__).parent)), CONTROLSHIFT_ALLOW_UNSAFE_FAISS="1")
    if r.returncode == 0:
        pytest.skip("faiss backend + torch no longer conflicts")
    assert "OMP: Error #15" in r.stderr


@darwin_only
def test_explicit_faiss_backend_is_refused_on_macos_with_a_controlled_error(tmp_path):
    """No process abort: the CLI exits 2 with an actionable message before loading any model."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("CONTROLSHIFT_ALLOW_UNSAFE_FAISS", "CONTROLSHIFT_DENSE_BACKEND")}
    for mode in ("dense", "hybrid", "hybrid_rerank"):
        r = subprocess.run(
            [sys.executable, "-W", "ignore", "-m", "controlshift.retrieval.cli", "--db",
             str(tmp_path / "x.db"), "--index-dir", str(tmp_path), "search", "q", "--mode", mode,
             "--dense-backend", "faiss"], capture_output=True, text=True, env=env, check=False)
        assert r.returncode == 2, (mode, r.returncode, r.stderr[-300:])
        assert "disabled on macOS" in r.stderr and "--dense-backend numpy" in r.stderr
        assert "Fatal Python error" not in r.stderr  # a controlled exit, not an abort
