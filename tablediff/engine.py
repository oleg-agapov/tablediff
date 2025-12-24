from __future__ import annotations

from typing import Iterable

from tablediff.adapters.base import Adapter, TableMeta
from tablediff.models import DiffCounts, DiffResult


class DiffError(ValueError):
    pass


class DiffEngine:
    def __init__(self, adapter: Adapter) -> None:
        self.adapter = adapter

    def _validate_columns(self, table: str, columns: Iterable[str]) -> list[str]:
        cols = list(columns)
        if not cols:
            raise DiffError(f"Table '{table}' not found or has no columns.")
        return cols

    def _get_columns(self, table: str) -> list[str]:
        return self._validate_columns(table, self.adapter.get_columns(table))

    def _validate_primary_key(self, table: str, pk: str, columns: Iterable[str]) -> None:
        if pk not in columns:
            raise DiffError(f"Primary key '{pk}' not found in table '{table}'.")

    def _common_columns(self, cols_a: Iterable[str], cols_b: Iterable[str]) -> list[str]:
        common_columns = sorted(set(cols_a).intersection(cols_b))
        if not common_columns:
            raise DiffError("No common columns between the two tables.")
        return common_columns

    def _check_duplicate_pks(self, table: str, pk: str) -> None:
        dup_count = self.adapter.count_duplicate_pks(table, pk)
        if dup_count > 0:
            raise DiffError(f"Table '{table}' has {dup_count} duplicate primary key values.")

    def _build_counts(
        self,
        table_a: str,
        table_b: str,
        pk: str,
        common_columns: list[str],
    ) -> DiffCounts:
        counts_dict = self.adapter.diff_counts(table_a, table_b, pk, common_columns)
        return DiffCounts(
            only_in_a=counts_dict["only_in_a"],
            only_in_b=counts_dict["only_in_b"],
            in_both_same=counts_dict["in_both_same"],
            in_both_diff=counts_dict["in_both_diff"],
        )

    def _build_meta(self, table: str, columns: list[str]) -> TableMeta:
        return TableMeta(
            name=table,
            columns=columns,
            row_count=self.adapter.count_rows(table),
        )

    def diff(self, table_a: str, table_b: str, pk: str) -> DiffResult:
        cols_a = self._get_columns(table_a)
        cols_b = self._get_columns(table_b)

        self._validate_primary_key(table_a, pk, cols_a)
        self._validate_primary_key(table_b, pk, cols_b)

        common_columns = self._common_columns(cols_a, cols_b)

        self._check_duplicate_pks(table_a, pk)
        self._check_duplicate_pks(table_b, pk)

        counts = self._build_counts(table_a, table_b, pk, common_columns)
        meta_a = self._build_meta(table_a, cols_a)
        meta_b = self._build_meta(table_b, cols_b)

        return DiffResult(
            table_a=meta_a,
            table_b=meta_b,
            primary_key=pk,
            common_columns=common_columns,
            counts=counts,
        )


def diff_tables(adapter: Adapter, table_a: str, table_b: str, pk: str) -> DiffResult:
    return DiffEngine(adapter).diff(table_a, table_b, pk)
