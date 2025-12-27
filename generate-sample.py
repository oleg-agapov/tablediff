from __future__ import annotations

import argparse
from pathlib import Path
import duckdb
from tablediff.adapters.duckdb import DuckDBAdapter
from tests.conftest import SAMPLE_DB_STATEMENTS


def generate_duckdb_example(db_path: str) -> None:
    path = Path(db_path)
    if path.exists():
        path.unlink()
    db = DuckDBAdapter(duckdb.connect(db_path))
    db.run_statements(SAMPLE_DB_STATEMENTS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a sample DuckDB database at the provided path.")
    parser.add_argument("--db-path", required=True, help="Output path for the DuckDB database (e.g. data/example.duckdb).")
    args = parser.parse_args()
    generate_duckdb_example(args.db_path)


if __name__ == "__main__":
    main()
