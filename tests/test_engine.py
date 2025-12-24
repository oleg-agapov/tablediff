from __future__ import annotations

import duckdb
import pytest

from tablediff.adapters.duckdb import DuckDBAdapter
from tablediff.engine import DiffError, diff_tables


def _create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE a (
            id INTEGER,
            name TEXT,
            value INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE b (
            id INTEGER,
            name TEXT,
            value INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO a VALUES
            (1, 'alpha', 10),
            (2, 'beta', 20),
            (3, 'gamma', 30),
            (5, 'epsilon', 50)
        """
    )
    conn.execute(
        """
        INSERT INTO b VALUES
            (1, 'alpha', 10),
            (2, 'beta', 25),
            (4, 'delta', 40),
            (5, 'epsilon', 50)
        """
    )


def test_diff_counts(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    _create_tables(conn)
    conn.close()

    adapter = DuckDBAdapter(str(db_path))
    result = diff_tables(adapter, "a", "b", "id")

    assert result.counts.only_in_a == 1
    assert result.counts.only_in_b == 1
    assert result.counts.in_both_same == 2
    assert result.counts.in_both_diff == 1


def test_duplicate_pk_validation(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "dup.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE a (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE b (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO a VALUES (1, 'alpha'), (1, 'alpha-dup')")
    conn.execute("INSERT INTO b VALUES (1, 'alpha')")
    conn.close()

    adapter = DuckDBAdapter(str(db_path))
    with pytest.raises(DiffError, match="duplicate primary key"):
        diff_tables(adapter, "a", "b", "id")
