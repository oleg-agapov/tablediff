from __future__ import annotations

from collections.abc import Callable, Iterable
from tablediff.adapters.duckdb import DuckDBAdapter


def test_get_columns(duckdb_ab_adapter: DuckDBAdapter) -> None:
    adapter = duckdb_ab_adapter
    assert adapter.get_columns("a") == ["id", "name", "value", "col_in_a"]


def test_count_rows(duckdb_ab_adapter: DuckDBAdapter) -> None:
    adapter = duckdb_ab_adapter
    assert adapter.count_rows("a") == 5


def test_count_duplicate_pks(
    duckdb_adapter: Callable[[Iterable[str]], DuckDBAdapter],
) -> None:
    adapter = duckdb_adapter(
        [
            "CREATE TABLE items (id INTEGER, name TEXT)",
            "INSERT INTO items VALUES (1, 'alpha'), (1, 'beta'), (2, 'gamma')",
        ],
    )

    assert adapter.count_duplicate_pks("items", "id") == 1


def test_diff_counts(duckdb_ab_adapter: DuckDBAdapter) -> None:
    adapter = duckdb_ab_adapter

    result = adapter.diff_counts("a", "b", "id", ["name", "value"])

    assert result == {
        "only_in_a": 1,
        "only_in_b": 1,
        "in_both_same": 2,
        "in_both_diff": 2,
    }
