"""`controlshift-db` command line: build, inspect, validate and query the knowledge store."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loader import LoadError, build_database
from .queries import KnowledgeStore, NotFoundError
from .schema import TABLES, connect
from .validate import validate_database

DEFAULT_DB = Path("data/processed/controlshift.db")
DEFAULT_PROCESSED = Path("data/processed")


def _dump(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="controlshift-db", description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="(re)build the database from data/processed JSONL, atomically")
    sub.add_parser("inspect", help="print table row counts and mapping summary")
    sub.add_parser("validate", help="integrity + manifest consistency checks (exit 1 on problems)")
    g = sub.add_parser("get", help="show one control")
    g.add_argument("element_id"); g.add_argument("--version", required=True)
    m = sub.add_parser("map", help="official crosswalk rows for a control")
    m.add_argument("element_id")
    m.add_argument("--version", required=True, help="2.0 = forward lookup, 1.1 = reverse lookup")
    e = sub.add_parser("evidence", help="chunks supporting a control")
    e.add_argument("element_id"); e.add_argument("--version", required=True)
    c = sub.add_parser("category", help="list subcategories of a category")
    c.add_argument("category_id"); c.add_argument("--version", required=True)
    n = sub.add_parser("unmapped", help="2.0 controls with no 1.1 mapping (or 1.1 with no 2.0)")
    n.add_argument("--direction", choices=["no-earlier", "no-later", "flagged-new"], default="no-earlier")
    n.add_argument("--level", choices=["function", "category", "subcategory"])
    args = ap.parse_args(argv)

    try:
        if args.cmd == "build":
            _dump(build_database(args.db, args.processed_dir))
            return 0
        if args.cmd == "validate":
            problems = validate_database(args.db, args.processed_dir)
            for p in problems:
                print(f"PROBLEM: {p}", file=sys.stderr)
            print("database valid" if not problems else f"{len(problems)} problem(s)")
            return 1 if problems else 0
        if args.cmd == "inspect":
            conn = connect(args.db, readonly=True)
            _dump({
                "tables": {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                           for t in TABLES},
                "elements": [dict(r) for r in conn.execute(
                    "SELECT version, level, COUNT(*) AS n FROM element GROUP BY 1,2 ORDER BY 1,2")],
                "crosswalk_by_type": {r[0]: r[1] for r in conn.execute(
                    "SELECT mapping_type, COUNT(*) FROM crosswalk_mapping GROUP BY 1 ORDER BY 1")},
            })
            return 0
        with KnowledgeStore(args.db) as store:
            if args.cmd == "get":
                result = store.get_control(args.element_id, args.version)
                if result is None:
                    raise NotFoundError(f"{args.element_id} not found in CSF {args.version}")
            elif args.cmd == "map":
                result = (store.mappings_2_0_to_1_1(args.element_id) if args.version == "2.0"
                          else store.mappings_1_1_to_2_0(args.element_id))
            elif args.cmd == "evidence":
                result = store.get_evidence(args.element_id, args.version)
            elif args.cmd == "category":
                result = store.list_controls_in_category(args.category_id, args.version)
            elif args.direction == "flagged-new":
                result = store.controls_flagged_new_in_2_0()
            else:
                fn = (store.controls_without_earlier_mapping if args.direction == "no-earlier"
                      else store.controls_without_later_mapping)
                result = fn(args.level)
            _dump(result)
        return 0
    except (LoadError, NotFoundError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
