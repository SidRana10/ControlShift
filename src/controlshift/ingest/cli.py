"""`controlshift-ingest` command line entry point."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import IngestionError
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="controlshift-ingest", description=__doc__)
    ap.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    ap.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    ap.add_argument("--strict", action="store_true", help="exit non-zero if validation warns")
    args = ap.parse_args(argv)
    try:
        manifest = run(args.raw_dir, args.out_dir)
    except IngestionError as exc:
        print(f"ingestion failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest["counts"], indent=2))
    for w in manifest["warnings"]:
        print(f"WARNING: {w}", file=sys.stderr)
    print(f"wrote {args.out_dir}/chunks.jsonl, crosswalk.jsonl, manifest.json")
    return 1 if (args.strict and manifest["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
