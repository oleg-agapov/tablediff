from __future__ import annotations

import argparse
import sys

from tablediff.adapters.default import DefaultAdapter
from tablediff.diffing import DiffError, diff_tables
from tablediff.renderers.summary import render_summary


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="tablediff",
        description="Compare two database tables by primary key.",
    )
    parser.add_argument(
        "table_a",
        help="First table name.",
    )
    parser.add_argument(
        "table_b",
        help="Second table name.",
    )
    parser.add_argument(
        "--pk",
        required=True,
        help="Primary key column name.",
    )
    parser.add_argument(
        "--conn",
        required=True,
        help="Database connection string or file path for DuckDB.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        adapter = DefaultAdapter(args.conn)
        result = diff_tables(adapter, args.table_a, args.table_b, args.pk)
        print(render_summary(result))
    except DiffError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
