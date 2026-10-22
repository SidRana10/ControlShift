from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


@pytest.fixture(scope="session")
def raw_dir() -> Path:
    needed = ["nist_csf_1_1.pdf", "nist_csf_2_0.pdf", "nist_csf_transition.xlsx"]
    if not all((RAW / n).is_file() for n in needed):
        pytest.skip("real NIST files not present in data/raw")
    return RAW


@pytest.fixture(scope="session")
def ingested(raw_dir, tmp_path_factory):
    from controlshift.ingest.pipeline import run

    out = tmp_path_factory.mktemp("processed")
    manifest = run(raw_dir, out)
    return out, manifest


@pytest.fixture(scope="session")
def real_db(ingested, tmp_path_factory):
    """Database built from the real NIST data (processed dir from the `ingested` fixture)."""
    from controlshift.store.loader import build_database

    processed, _ = ingested
    db = tmp_path_factory.mktemp("db") / "controlshift.db"
    counts = build_database(db, processed)
    return db, processed, counts
