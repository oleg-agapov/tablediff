from __future__ import annotations

import argparse
import os
from tablediff.engine import table_diff, schema_diff, load_csv_to_duckdb
from tablediff.renderers import render_summary_table, render_extended_table, render_schema_diff

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tablediff",
        description="Compare two database tables by primary key.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_conn_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--conn", help="Database connection string for table_a (or both tables if --conn2 not provided).")
        subparser.add_argument("--conn2", help="Database connection string for table_b (when comparing across different databases).")
        subparser.add_argument("--dbt-profile-path", default="profiles.yml", help="Path to dbt profiles file.")
        subparser.add_argument("--dbt-profile", default="dbt_analytics", help="Profile name inside the profiles.yml file.")
        subparser.add_argument("--dbt-target", default="dev", help="Target name defined in the dbt profile.")
        subparser.add_argument("--env-file", default=".env", help="Path to a .env file that stores credential values.")

    compare_parser = subparsers.add_parser("compare", help="Compare two database tables by primary key.")
    compare_parser.add_argument("table_a", help="First table name.")
    compare_parser.add_argument("table_b", help="Second table name.")
    compare_parser.add_argument("--pk", required=True, help="Primary key column name.")
    add_conn_args(compare_parser)
    compare_parser.add_argument("--extended", action="store_true", help="Enable extended output")
    compare_parser.add_argument("--where", help="SQL WHERE clause to filter rows before comparison (e.g., \"status = 'active'\")")

    schema_parser = subparsers.add_parser("schema", help="Compare schemas (data types) without comparing data.")
    schema_parser.add_argument("table_a", help="First table name.")
    schema_parser.add_argument("table_b", help="Second table name.")
    add_conn_args(schema_parser)

    files_parser = subparsers.add_parser("files", help="Compare two CSV files by primary key.")
    files_parser.add_argument("file_a", help="First CSV file path.")
    files_parser.add_argument("file_b", help="Second CSV file path.")
    files_parser.add_argument("--pk", required=True, help="Primary key column name.")
    files_parser.add_argument("--extended", action="store_true", help="Enable extended output")
    files_parser.add_argument("--where", help="SQL WHERE clause to filter rows before comparison (e.g., \"status = 'active'\")")
    return parser


def _sanitize_table_name(name: str, fallback: str) -> str:
    sanitized = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in name)
    if not sanitized:
        sanitized = fallback
    if not (sanitized[0].isalpha() or sanitized[0] == "_"):
        sanitized = f"{fallback}_{sanitized}"
    return sanitized


def _derive_csv_table_names(csv_path_a: str, csv_path_b: str) -> tuple[str, str]:
    base_a = os.path.basename(csv_path_a)
    base_b = os.path.basename(csv_path_b)
    name_a = _sanitize_table_name(base_a, "table_a")
    name_b = _sanitize_table_name(base_b, "table_b")
    if name_a == name_b:
        return f"{name_a}_1", f"{name_b}_2"
    return name_a, name_b


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    temp_db_path = None
    try:
        if args.command == "compare":
            # Determine connection strings for each table
            # --conn is used for table_a (and table_b if --conn2 is not provided)
            # --conn2 is used for table_b when comparing across different databases
            conn_a = args.conn
            conn_b = args.conn2 if args.conn2 else args.conn
            table_a_name = args.table_a
            table_b_name = args.table_b

            results = table_diff(conn_a, conn_b, table_a_name, table_b_name, args.pk, where=args.where)
            render_summary_table(results)
            if args.extended:
                render_extended_table(results)
                schema_result = schema_diff(conn_a, conn_b, table_a_name, table_b_name)
                render_schema_diff(schema_result)
        elif args.command == "schema":
            conn_a = args.conn
            conn_b = args.conn2 if args.conn2 else args.conn
            table_a_name = args.table_a
            table_b_name = args.table_b

            result = schema_diff(conn_a, conn_b, table_a_name, table_b_name)
            render_schema_diff(result)
        elif args.command == "files":
            csv_path_a = args.file_a
            csv_path_b = args.file_b

            if not os.path.exists(csv_path_a):
                parser.error(f"CSV file not found: {csv_path_a}")
            if not os.path.exists(csv_path_b):
                parser.error(f"CSV file not found: {csv_path_b}")

            table_a_name, table_b_name = _derive_csv_table_names(csv_path_a, csv_path_b)
            conn_str, temp_db_path = load_csv_to_duckdb(
                csv_path_a,
                csv_path_b,
                table_name_a=table_a_name,
                table_name_b=table_b_name,
            )
            conn_a = conn_str
            conn_b = conn_str

            results = table_diff(conn_a, conn_b, table_a_name, table_b_name, args.pk, where=args.where)
            render_summary_table(results)
            if args.extended:
                render_extended_table(results)
                schema_result = schema_diff(conn_a, conn_b, table_a_name, table_b_name)
                render_schema_diff(schema_result)
        else:
            parser.error("Unknown command")
    finally:
        # Clean up temporary database file if created
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.unlink(temp_db_path)
            except (FileNotFoundError, PermissionError, OSError) as e:
                # Ignore cleanup errors - the file will be cleaned up by the OS eventually
                pass
