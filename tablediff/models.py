from __future__ import annotations

from dataclasses import dataclass

from tablediff.adapters.base import TableMeta


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
