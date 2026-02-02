from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb

PARAMS_BLOCK_RE = re.compile(r"(?s)-- params:start\n.*?-- params:end\n")


def build_params_block(
    prod_rows: int,
    dev_remove_rows: int,
    dev_add_rows: int,
    dev_null_status_rows: int,
) -> str:
    return (
        "-- params:start\n"
        "CREATE OR REPLACE TEMP TABLE params AS\n"
        "SELECT\n"
        f"  {prod_rows}::INTEGER AS prod_rows,\n"
        f"  {dev_remove_rows}::INTEGER AS dev_remove_rows,\n"
        f"  {dev_add_rows}::INTEGER AS dev_add_rows,\n"
        f"  {dev_null_status_rows}::INTEGER AS dev_null_status_rows;\n"
        "-- params:end\n"
    )


def load_sql(
    sql_path: Path,
    prod_rows: int | None,
    dev_remove_rows: int | None,
    dev_add_rows: int | None,
    dev_null_status_rows: int | None,
) -> str:
    sql = sql_path.read_text(encoding="utf-8")
    if prod_rows is None and dev_remove_rows is None and dev_add_rows is None and dev_null_status_rows is None:
        return sql

    defaults = PARAMS_BLOCK_RE.search(sql)
    if not defaults:
        raise ValueError("Could not find params block in SQL file.")

    default_prod = int(re.search(r"(\d+)::INTEGER AS prod_rows", defaults.group(0)).group(1))
    default_remove = int(re.search(r"(\d+)::INTEGER AS dev_remove_rows", defaults.group(0)).group(1))
    default_add = int(re.search(r"(\d+)::INTEGER AS dev_add_rows", defaults.group(0)).group(1))
    default_null_status = int(re.search(r"(\d+)::INTEGER AS dev_null_status_rows", defaults.group(0)).group(1))

    params_block = build_params_block(
        prod_rows if prod_rows is not None else default_prod,
        dev_remove_rows if dev_remove_rows is not None else default_remove,
        dev_add_rows if dev_add_rows is not None else default_add,
        dev_null_status_rows if dev_null_status_rows is not None else default_null_status,
    )
    return PARAMS_BLOCK_RE.sub(params_block, sql)


def generate_database(
    db_path: Path,
    sql_path: Path,
    prod_rows: int | None,
    dev_remove_rows: int | None,
    dev_add_rows: int | None,
    dev_null_status_rows: int | None,
) -> None:
    if db_path.exists():
        db_path.unlink()
    sql = load_sql(sql_path, prod_rows, dev_remove_rows, dev_add_rows, dev_null_status_rows)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(sql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DuckDB database from the test data SQL script.")
    parser.add_argument("--db-path", required=True, help="Output path for the DuckDB database.")
    parser.add_argument(
        "--sql-path",
        default="scripts/generate_duckdb_test_data.sql",
        help="Path to the SQL script.",
    )
    parser.add_argument("--prod-rows", type=int, help="Number of rows to generate in users_prod.")
    parser.add_argument("--dev-remove-rows", type=int, help="Number of rows to remove from users_dev.")
    parser.add_argument("--dev-add-rows", type=int, help="Number of rows to add to users_dev.")
    parser.add_argument(
        "--dev-null-status-rows",
        type=int,
        help="Number of rows in users_dev to set status to NULL.",
    )
    args = parser.parse_args()

    generate_database(
        Path(args.db_path),
        Path(args.sql_path),
        args.prod_rows,
        args.dev_remove_rows,
        args.dev_add_rows,
        args.dev_null_status_rows,
    )


if __name__ == "__main__":
    main()
