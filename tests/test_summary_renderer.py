from __future__ import annotations

import duckdb
import pytest

from tablediff.adapters.duckdb import DuckDBAdapter
from tablediff.engine import diff_tables
from tablediff.renderers.summary import render_summary


def test_summary_output(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "summary.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE a (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE b (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO a VALUES (1, 'alpha')")
    conn.execute("INSERT INTO b VALUES (1, 'alpha')")
    conn.close()

    adapter = DuckDBAdapter(str(db_path))
    result = diff_tables(adapter, "a", "b", "id")
    output = render_summary(result)

    assert "Data diff summary" in output
    assert "Primary key: id" in output
    assert "Rows only in A: 0" in output
    assert "Rows in both (same): 1" in output
