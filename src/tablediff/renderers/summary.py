from __future__ import annotations

from tablediff.engine import DiffResult


def render_summary(result: DiffResult) -> str:
    only_in_a = sorted(set(result.table_a.columns) - set(result.table_b.columns))
    only_in_b = sorted(set(result.table_b.columns) - set(result.table_a.columns))
    common = result.common_columns

    def _format_list(items: list[str]) -> str:
        return f"({', '.join(items)})" if items else "()"

    lines = [
        "",
        "🔎 Data diff summary",
        "====================",
        f"🔑 Primary key: {result.primary_key}",
        "",
        "📚 Columns",
        f"- Table A columns: {len(result.table_a.columns)}",
        f"- Table B columns: {len(result.table_b.columns)}",
        f"- Only in A: {len(only_in_a)} {_format_list(only_in_a)}",
        f"- Only in B: {len(only_in_b)} {_format_list(only_in_b)}",
        f"- Common: {len(common)} {_format_list(common)}",
        "",
        "📊 Rows",
        f"- 📦 Table A rows: {result.table_a.row_count}",
        f"- 📦 Table B rows: {result.table_b.row_count}",
        f"- ➕ Rows only in A: {result.counts.only_in_a}",
        f"- ➕ Rows only in B: {result.counts.only_in_b}",
        f"- ✅ Rows in both (same): {result.counts.in_both_same}",
        f"- ⚠️  Rows in both (diff): {result.counts.in_both_diff}",
        "",
    ]
    return "\n".join(lines)
