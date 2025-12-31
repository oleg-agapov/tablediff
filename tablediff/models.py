from __future__ import annotations
from dataclasses import dataclass
from reladiff.diff_tables import DiffResultWrapper

@dataclass(frozen=True)
class TableMeta:
    name: str
    columns: list[str]
    rows: int

@dataclass(frozen=True)
class DiffResult:
    table_a: TableMeta
    table_b: TableMeta
    primary_key: str
    common_columns: list[str]
    rows_only_in_a: int
    rows_only_in_b: int
    rows_in_both_same: int
    rows_in_both_diff: int
    diff_by_keys: dict
    diff_by_sign: dict
    diffing: DiffResultWrapper
