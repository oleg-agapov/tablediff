from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True)
class TableMeta:
    name: str
    columns: list[str]
    row_count: int


class Adapter(Protocol):
    def get_columns(self, table: str) -> list[str]:
        ...

    def count_rows(self, table: str) -> int:
        ...

    def count_duplicate_pks(self, table: str, pk: str) -> int:
        ...

    def diff_counts(
        self, table_a: str, table_b: str, pk: str, common_columns: Iterable[str]
    ) -> dict[str, int]:
        ...

