from __future__ import annotations

import pytest

from tablediff.adapters.duckdb import DuckDBAdapter
from tablediff.engine import DiffError, diff_tables


def test_diff_counts(duckdb_ab_adapter: DuckDBAdapter) -> None:
    adapter = duckdb_ab_adapter
    result = diff_tables(adapter, "table_a", "table_b", "id")

    assert result.counts.only_in_a == 1
    assert result.counts.only_in_b == 1
    assert result.counts.in_both_same == 2
    assert result.counts.in_both_diff == 2


def test_duplicate_pk_validation(
    duckdb_adapter,
) -> None:
    adapter = duckdb_adapter(
        [
            "CREATE TABLE table_a (id INTEGER, name TEXT)",
            "CREATE TABLE table_b (id INTEGER, name TEXT)",
            "INSERT INTO table_a VALUES (1, 'alpha'), (1, 'alpha-dup')",
            "INSERT INTO table_b VALUES (1, 'alpha')",
        ]
    )
    with pytest.raises(DiffError, match="duplicate primary key"):
        diff_tables(adapter, "table_a", "table_b", "id")
