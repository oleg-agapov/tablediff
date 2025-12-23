from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

EXAMPLE_DATA: dict[str, list[dict[str, Any]]] = {
    "table_a": [
        {"id": 1, "name": "alpha", "value": 10, "col1": 1},
        {"id": 2, "name": "beta", "value": 20, "col1": 2},
        {"id": 3, "name": "gamma", "value": 30, "col1": 3},
        {"id": 5, "name": "epsilon", "value": 50, "col1": 4},
    ],
    "table_b": [
        {"id": 1, "name": "alpha", "value": 10},
        {"id": 2, "name": "beta", "value": 25},
        {"id": 4, "name": "delta", "value": 40},
        {"id": 5, "name": "epsilon", "value": 50},
    ],
}


def _duckdb_type_for(value: Any) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "DOUBLE"
    return "TEXT"


def _infer_schema(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    if not rows:
        raise ValueError("Example table has no rows.")
    columns = list(rows[0].keys())
    schema: list[tuple[str, str]] = []
    for col in columns:
        col_type = "TEXT"
        for row in rows:
            value = row.get(col)
            if value is not None:
                col_type = _duckdb_type_for(value)
                break
        schema.append((col, col_type))
    return schema


def generate_example_database(path: str, force: bool = False) -> Path:
    db_path = Path(path)
    if db_path.exists():
        if not force:
            raise FileExistsError(f"Database already exists: {db_path}")
        db_path.unlink()

    conn = duckdb.connect(str(db_path))
    try:
        for table_name, rows in EXAMPLE_DATA.items():
            schema = _infer_schema(rows)
            columns_sql = ", ".join(f"{name} {dtype}" for name, dtype in schema)
            conn.execute(f"CREATE TABLE {table_name} ({columns_sql})")

            columns = [name for name, _ in schema]
            placeholders = ", ".join(["?"] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            values = [[row.get(col) for col in columns] for row in rows]
            conn.executemany(insert_sql, values)
    finally:
        conn.close()

    return db_path

