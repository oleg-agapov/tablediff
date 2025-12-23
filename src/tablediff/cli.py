from __future__ import annotations

import argparse
import sys

from tablediff.adapters.duckdb import DuckDBAdapter
from tablediff.engine import DiffError, diff_tables
from tablediff.examples import generate_example_database
from tablediff.renderers.summary import render_summary


def _build_diff_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diff two DuckDB tables by primary key."
    )
    parser.add_argument("table_a", help="First table name.")
    parser.add_argument("table_b", help="Second table name.")
    parser.add_argument("--pk", required=True, help="Primary key column name.")
    parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB database file.",
    )
    return parser


def _build_example_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an example DuckDB database for tablediff demos."
    )
    parser.add_argument(
        "--db",
        default="data/example.duckdb",
        help="Output path for the example DuckDB database.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the database if it already exists.",
    )
    return parser


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "generate-example":
        parser = _build_example_parser()
        args = parser.parse_args(sys.argv[2:])
        try:
            db_path = generate_example_database(args.db, force=args.force)
        except FileExistsError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"Unexpected error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Example database created at: {db_path}")
        return

    parser = _build_diff_parser()
    args = parser.parse_args()

    try:
        adapter = DuckDBAdapter(args.db)
        result = diff_tables(adapter, args.table_a, args.table_b, args.pk)
    except DiffError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(render_summary(result))


if __name__ == "__main__":
    main()
