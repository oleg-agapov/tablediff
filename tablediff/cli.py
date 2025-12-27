from __future__ import annotations

import argparse

from tablediff.adapters.default import DefaultAdapter
from tablediff.engine import diff_tables
from tablediff.renderers.summary import render_summary_rich


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tablediff",
        description="Compare two database tables by primary key.",
    )
    parser.add_argument("table_a", help="First table name.")
    parser.add_argument("table_b", help="Second table name.")
    
    parser.add_argument("--pk", required=True, help="Primary key column name.")
    parser.add_argument("--conn", required=True, help="Database connection string or file path for DuckDB.")
    
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    adapter = DefaultAdapter(args.conn)
    result = diff_tables(adapter, args.table_a, args.table_b, args.pk)
    render_summary_rich(result)


if __name__ == "__main__":
    main()
