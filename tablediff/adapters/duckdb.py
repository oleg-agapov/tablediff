from __future__ import annotations

from typing import Iterable

import duckdb


def _quote_ident(name: str) -> str:
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


class DuckDBAdapter:
    def __init__(self, database: str | duckdb.DuckDBPyConnection) -> None:
        if isinstance(database, str):
            if database == ":memory:":
                self._conn = duckdb.connect(database)
            else:
                self._conn = duckdb.connect(database, read_only=True)
        else:
            self._conn = database

    def get_columns(self, table: str) -> list[str]:
        query = f"PRAGMA table_info({_quote_ident(table)})"
        rows = self._conn.execute(query).fetchall()
        return [row[1] for row in rows]

    def count_rows(self, table: str) -> int:
        query = f"SELECT COUNT(*) FROM {_quote_ident(table)}"
        return int(self._conn.execute(query).fetchone()[0])

    def count_duplicate_pks(self, table: str, pk: str) -> int:
        query = f"""
            SELECT COUNT(*) FROM (
                SELECT {_quote_ident(pk)} AS pk
                FROM {_quote_ident(table)}
                GROUP BY {_quote_ident(pk)}
                HAVING COUNT(*) > 1
            ) dup
        """
        return int(self._conn.execute(query).fetchone()[0])

    def diff_counts(
        self, table_a: str, table_b: str, pk: str, common_columns: Iterable[str]
    ) -> dict[str, int]:
        col_checks = []
        for col in common_columns:
            col_q = _quote_ident(col)
            col_checks.append(f"a.{col_q} IS NOT DISTINCT FROM b.{col_q}")
        all_equal = " AND ".join(col_checks)

        pk_q = _quote_ident(pk)
        query = f"""
            SELECT
                SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NULL THEN 1 ELSE 0 END) AS only_in_a,
                SUM(CASE WHEN a.{pk_q} IS NULL AND b.{pk_q} IS NOT NULL THEN 1 ELSE 0 END) AS only_in_b,
                SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NOT NULL AND ({all_equal}) THEN 1 ELSE 0 END) AS in_both_same,
                SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NOT NULL AND NOT ({all_equal}) THEN 1 ELSE 0 END) AS in_both_diff
            FROM {_quote_ident(table_a)} AS a
            FULL OUTER JOIN {_quote_ident(table_b)} AS b
            ON a.{pk_q} = b.{pk_q}
        """
        row = self._conn.execute(query).fetchone()
        return {
            "only_in_a": int(row[0]),
            "only_in_b": int(row[1]),
            "in_both_same": int(row[2]),
            "in_both_diff": int(row[3]),
        }
