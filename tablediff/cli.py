from __future__ import annotations

import argparse
from tablediff.engine import table_diff
from tablediff.renderers import render_summary_table, render_extended_table

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tablediff",
        description="Compare two database tables by primary key.",
    )
    parser.add_argument("table_a", help="First table name.")
    parser.add_argument("table_b", help="Second table name.")

    parser.add_argument("--pk", required=True, help="Primary key column name.")
    parser.add_argument("--conn", help="Database connection string for table_a (or both tables if --conn2 not provided).")
    parser.add_argument("--conn2", help="Database connection string for table_b (when comparing across different databases).")
    parser.add_argument("--dbt-profile-path", default="profiles.yml", help="Path to dbt profiles file.")
    parser.add_argument("--dbt-profile", default="dbt_analytics", help="Profile name inside the profiles.yml file.")
    parser.add_argument("--dbt-target", default="dev", help="Target name defined in the dbt profile.")
    parser.add_argument("--env-file", default=".env", help="Path to a .env file that stores credential values.")
    parser.add_argument("--extended", action="store_true", help="Enable extended output")
    parser.add_argument("--where", help="SQL WHERE clause to filter rows before comparison (e.g., \"status = 'active'\")")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    # Determine connection strings for each table
    # --conn is used for table_a (and table_b if --conn2 is not provided)
    # --conn2 is used for table_b when comparing across different databases
    conn_a = args.conn
    conn_b = args.conn2 if args.conn2 else args.conn
    
    results = table_diff(conn_a, conn_b, args.table_a, args.table_b, args.pk, where=args.where)
    render_summary_table(results)
    if args.extended:
        render_extended_table(results)
