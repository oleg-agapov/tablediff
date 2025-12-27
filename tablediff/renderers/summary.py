from __future__ import annotations

from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

from tablediff.models import DiffResult


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
        "📊 Columns",
        f"- Table A columns: {len(result.table_a.columns)}",
        f"- Table B columns: {len(result.table_b.columns)}",
        f"- Only in A: {len(only_in_a)} {_format_list(only_in_a)}",
        f"- Only in B: {len(only_in_b)} {_format_list(only_in_b)}",
        f"- Common: {len(common)} {_format_list(common)}",
        "",
        "📚 Rows",
        f"- Table A rows: {result.table_a.row_count}",
        f"- Table B rows: {result.table_b.row_count}",
        f"- Rows only in A: {result.counts.only_in_a}",
        f"- Rows only in B: {result.counts.only_in_b}",
        f"- ✅ Rows in both (same): {result.counts.in_both_same}",
        f"- ⚠️  Rows in both (diff): {result.counts.in_both_diff}",
        "",
    ]
    return "\n".join(lines)


def render_summary_rich(result: DiffResult) -> None:
    only_in_a = sorted(set(result.table_a.columns) - set(result.table_b.columns))
    only_in_b = sorted(set(result.table_b.columns) - set(result.table_a.columns))
    common = result.common_columns

    console = Console()
    console.print()
    
    #console.print(Panel.fit(f"🔑 Primary key: {result.primary_key}", padding=(0, 2)))

    table = Table(show_header=True, padding=(0, 2), box=box.MINIMAL)
    table.add_column("Metric")
    table.add_column(result.table_a.name, justify="right")
    table.add_column(result.table_b.name, justify="right")

    table.add_row("Columns total", str(len(result.table_a.columns)), str(len(result.table_b.columns)))
    table.add_row("⚠️  Columns only", str(len(only_in_a)), str(len(only_in_b)))

    table.add_row("✅ Columns common", str(len(common)))
    table.add_row("", end_section=True)
    
    table.add_row("Rows total", str(result.table_a.row_count), str(result.table_b.row_count))
    table.add_row("⚠️  Rows only", str(result.counts.only_in_a), str(result.counts.only_in_b))
    table.add_row("✅ Rows in both (same)", str(result.counts.in_both_same))
    table.add_row("⚠️  Rows in both (diff)", str(result.counts.in_both_diff))
    
    console.print(Panel.fit(table, padding=(1, 2), title="🔎 Data diff summary"))
    console.print()
