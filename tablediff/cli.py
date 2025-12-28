from __future__ import annotations

import argparse
import os
from pathlib import Path

from tablediff.adapters.default import DefaultAdapter
from tablediff.adapters.snowflake import SnowflakeAdapter
from tablediff.engine import diff_tables
from tablediff.renderers.summary import render_summary_rich


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            # Always overwrite so the CLI uses the credentials from the file explicitly provided.
            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tablediff",
        description="Compare two database tables by primary key.",
    )
    parser.add_argument("table_a", help="First table name.")
    parser.add_argument("table_b", help="Second table name.")

    parser.add_argument("--pk", required=True, help="Primary key column name.")
    parser.add_argument(
        "--adapter",
        choices=["duckdb", "snowflake"],
        default="duckdb",
        help="Adapter backend to use.",
    )
    parser.add_argument(
        "--conn",
        help="Database connection string or file path for DuckDB.",
    )
    parser.add_argument(
        "--profile-path",
        default="profiles.yml",
        help="Path to dbt profiles file when using Snowflake.",
    )
    parser.add_argument(
        "--profile",
        default="hiive_analytics",
        help="Profile name inside the profiles.yml file when using Snowflake.",
    )
    parser.add_argument(
        "--target",
        default="dev",
        help="Target name defined in the dbt profile when using Snowflake.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file that stores the Snowflake credential values.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.adapter == "duckdb":
        if not args.conn:
            parser.error("--conn is required when adapter is set to 'duckdb'.")
        adapter = DefaultAdapter(args.conn)
    else:
        load_env_file(args.env_file)
        adapter = SnowflakeAdapter.from_profile(
            profile_path=args.profile_path,
            profile_name=args.profile,
            target_name=args.target,
        )

    result = diff_tables(adapter, args.table_a, args.table_b, args.pk)
    render_summary_rich(result)


if __name__ == "__main__":
    main()
