from __future__ import annotations

from collections.abc import Callable, Iterable

import duckdb
import pytest

from tablediff.adapters.duckdb import DuckDBAdapter

_AB_TABLE_STATEMENTS = [
    """
    CREATE TABLE a (
        id INTEGER,
        name TEXT,
        value INTEGER
    )
    """,
    """
    CREATE TABLE b (
        id INTEGER,
        name TEXT,
        value INTEGER
    )
    """,
    """
    INSERT INTO a VALUES
        (1, 'alpha', 10),
        (2, 'beta', 20),
        (3, 'gamma', 30),
        (5, 'epsilon', 50)
    """,
    """
    INSERT INTO b VALUES
        (1, 'alpha', 10),
        (2, 'beta', 25),
        (4, 'delta', 40),
        (5, 'epsilon', 50)
    """,
]


@pytest.fixture
def duckdb_adapter() -> Callable[[Iterable[str]], DuckDBAdapter]:
    def _make_adapter(statements: Iterable[str]) -> DuckDBAdapter:
        conn = duckdb.connect(":memory:")
        for statement in statements:
            conn.execute(statement)
        return DuckDBAdapter(conn)

    return _make_adapter


@pytest.fixture
def duckdb_ab_adapter(duckdb_adapter: Callable[[Iterable[str]], DuckDBAdapter]) -> DuckDBAdapter:
    return duckdb_adapter(_AB_TABLE_STATEMENTS)
