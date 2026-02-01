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
    parser.add_argument("table_a", help="First table name.")
    parser.add_argument("table_b", help="Second table name.")

    parser.add_argument("--pk", help="Primary key column name (required unless --schema-only is used).")
    parser.add_argument("--conn", help="Database connection string for table_a (or both tables if --conn2 not provided).")
    parser.add_argument("--conn2", help="Database connection string for table_b (when comparing across different databases).")
    parser.add_argument("--csv", action="store_true", help="Treat table_a and table_b as CSV file paths instead of table names.")
    parser.add_argument("--dbt-profile-path", default="profiles.yml", help="Path to dbt profiles file.")
    parser.add_argument("--dbt-profile", default="dbt_analytics", help="Profile name inside the profiles.yml file.")
    parser.add_argument("--dbt-target", default="dev", help="Target name defined in the dbt profile.")
    parser.add_argument("--env-file", default=".env", help="Path to a .env file that stores credential values.")
    parser.add_argument("--extended", action="store_true", help="Enable extended output")
    parser.add_argument("--where", help="SQL WHERE clause to filter rows before comparison (e.g., \"status = 'active'\")")
    parser.add_argument("--schema-only", action="store_true", help="Only compare schemas (data types) without comparing data")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    # Validate that --pk is provided when not using --schema-only
    if not args.schema_only and not args.pk:
        parser.error("--pk is required unless --schema-only is used")
    
    # Handle CSV mode
    temp_db_path = None
    if args.csv:
        # In CSV mode, table_a and table_b are CSV file paths
        csv_path_a = args.table_a
        csv_path_b = args.table_b
        
        # Validate that CSV files exist
        if not os.path.exists(csv_path_a):
            parser.error(f"CSV file not found: {csv_path_a}")
        if not os.path.exists(csv_path_b):
            parser.error(f"CSV file not found: {csv_path_b}")
        
        # Load CSV files into temporary DuckDB database
        conn_str, temp_db_path = load_csv_to_duckdb(csv_path_a, csv_path_b)
        conn_a = conn_str
        conn_b = conn_str
        table_a_name = "table_a"
        table_b_name = "table_b"
    else:
        # Determine connection strings for each table
        # --conn is used for table_a (and table_b if --conn2 is not provided)
        # --conn2 is used for table_b when comparing across different databases
        conn_a = args.conn
        conn_b = args.conn2 if args.conn2 else args.conn
        table_a_name = args.table_a
        table_b_name = args.table_b
    
    try:
        if args.schema_only:
            # Perform schema-only comparison
            result = schema_diff(conn_a, conn_b, table_a_name, table_b_name)
            render_schema_diff(result)
        else:
            # Perform full data comparison
            results = table_diff(conn_a, conn_b, table_a_name, table_b_name, args.pk, where=args.where)
            render_summary_table(results)
            if args.extended:
                render_extended_table(results)
                # Also show schema comparison in extended output
                schema_result = schema_diff(conn_a, conn_b, table_a_name, table_b_name)
                render_schema_diff(schema_result)
    finally:
        # Clean up temporary database file if created
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.unlink(temp_db_path)
            except (FileNotFoundError, PermissionError, OSError) as e:
                # Ignore cleanup errors - the file will be cleaned up by the OS eventually
                pass
