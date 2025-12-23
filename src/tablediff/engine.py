from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tablediff.adapters.base import Adapter, TableMeta


@dataclass(frozen=True)
class DiffCounts:
    only_in_a: int
    only_in_b: int
    in_both_same: int
    in_both_diff: int


@dataclass(frozen=True)
class DiffResult:
    table_a: TableMeta
    table_b: TableMeta
    primary_key: str
    common_columns: list[str]
    counts: DiffCounts


class DiffError(ValueError):
    pass


def _validate_columns(table: str, columns: Iterable[str]) -> list[str]:
    cols = list(columns)
    if not cols:
        raise DiffError(f"Table '{table}' not found or has no columns.")
    return cols


def diff_tables(adapter: Adapter, table_a: str, table_b: str, pk: str) -> DiffResult:
    cols_a = _validate_columns(table_a, adapter.get_columns(table_a))
    cols_b = _validate_columns(table_b, adapter.get_columns(table_b))

    if pk not in cols_a:
        raise DiffError(f"Primary key '{pk}' not found in table '{table_a}'.")
    if pk not in cols_b:
        raise DiffError(f"Primary key '{pk}' not found in table '{table_b}'.")

    common_columns = sorted(set(cols_a).intersection(cols_b))
    if not common_columns:
        raise DiffError("No common columns between the two tables.")

    dup_a = adapter.count_duplicate_pks(table_a, pk)
    if dup_a > 0:
        raise DiffError(f"Table '{table_a}' has {dup_a} duplicate primary key values.")
    dup_b = adapter.count_duplicate_pks(table_b, pk)
    if dup_b > 0:
        raise DiffError(f"Table '{table_b}' has {dup_b} duplicate primary key values.")

    counts_dict = adapter.diff_counts(table_a, table_b, pk, common_columns)
    counts = DiffCounts(
        only_in_a=counts_dict["only_in_a"],
        only_in_b=counts_dict["only_in_b"],
        in_both_same=counts_dict["in_both_same"],
        in_both_diff=counts_dict["in_both_diff"],
    )

    meta_a = TableMeta(
        name=table_a,
        columns=cols_a,
        row_count=adapter.count_rows(table_a),
    )
    meta_b = TableMeta(
        name=table_b,
        columns=cols_b,
        row_count=adapter.count_rows(table_b),
    )

    return DiffResult(
        table_a=meta_a,
        table_b=meta_b,
        primary_key=pk,
        common_columns=common_columns,
        counts=counts,
    )

