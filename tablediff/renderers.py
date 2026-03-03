from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tablediff.models import DiffResult, SchemaDiffResult


def _format_list(items: list[str]) -> str:
    return f"{', '.join(items)}" if items else "-"


def render_summary(result: DiffResult) -> str:
    cols_only_in_a = sorted(set(result.table_a.columns) - set(result.table_b.columns))
    cols_only_in_b = sorted(set(result.table_b.columns) - set(result.table_a.columns))

    lines = [
        "",
        "🔎 Data diff summary",
        "====================",
        f"🔑 Primary key: {result.primary_key}",
        "",
        "📊 Columns",
        f"- Table A columns: {len(result.table_a.columns)}",
        f"- Table B columns: {len(result.table_b.columns)}",
        f"- Only in A: {len(cols_only_in_a)} {_format_list(cols_only_in_a)}",
        f"- Only in B: {len(cols_only_in_a)} {_format_list(cols_only_in_b)}",
        f"- Common: {len(result.common_columns)} {_format_list(result.common_columns)}",
        "",
        "📚 Rows",
        f"- Table A rows: {result.table_a.rows}",
        f"- Table B rows: {result.table_b.rows}",
        f"- Rows only in A: {result.rows_only_in_a}",
        f"- Rows only in B: {result.rows_only_in_b}",
        f"- ✅ Rows in both (same): {result.rows_in_both_same}",
        f"- ⚠️  Rows in both (diff): {result.rows_in_both_diff}",
        "",
    ]
    return "\n".join(lines)


def render_summary_table(result: DiffResult) -> None:
    cols_only_in_a = sorted(set(result.table_a.columns) - set(result.table_b.columns))
    cols_only_in_b = sorted(set(result.table_b.columns) - set(result.table_a.columns))

    console = Console()
    console.print()

    table = Table(show_header=True, padding=(0, 2), box=box.MINIMAL)
    table.add_column("Metric")
    table.add_column(result.table_a.name, justify="right")
    table.add_column(result.table_b.name, justify="right")

    table.add_row("Columns total", str(len(result.table_a.columns)), str(len(result.table_b.columns)), style="blue")
    table.add_row("→ Columns common", str(len(result.common_columns)), str(len(result.common_columns)), style="green")
    table.add_row("→ Columns only", str(len(cols_only_in_a)), str(len(cols_only_in_b)), style="yellow")

    table.add_row("", end_section=True)

    table.add_row("Rows total", str(result.table_a.rows), str(result.table_b.rows), style="blue")
    table.add_row("→ Rows in both (same)", str(result.rows_in_both_same), str(result.rows_in_both_same), style="green")
    table.add_row("→ Rows in both (diff)", str(result.rows_in_both_diff), str(result.rows_in_both_diff), style="yellow")
    table.add_row("→ Rows only", str(result.rows_only_in_a), str(result.rows_only_in_b), style="green")

    console.print(Panel.fit(table, padding=(1, 2), title="🔎 Data diff summary"))
    console.print()


def render_extended_table(result: DiffResult) -> None:
    console = Console()
    cols_only_in_a = sorted(set(result.table_a.columns) - set(result.table_b.columns))
    cols_only_in_b = sorted(set(result.table_b.columns) - set(result.table_a.columns))

    # def _format_list(items: list[str]) -> str:
    #     return f"({', '.join(items)})" if items else "()"

    def _format_keys_sample(keys: list[tuple], limit: int = 5) -> str:
        sample = keys[:limit]
        if not sample:
            return "()"
        rendered = []
        for key in sample:
            if isinstance(key, tuple):
                key_list = list(key)
            elif isinstance(key, list):
                key_list = key
            else:
                key_list = [key]
            rendered.append(repr(key_list))
        return ", ".join(rendered)

    console.print()

    table = Table(show_header=False, box=box.MINIMAL, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Primary key", str(result.primary_key), style="blue")
    common_columns_count = len(result.common_columns)
    common_columns_string = _format_list(result.common_columns)
    table.add_row("Columns common", f"[{common_columns_count}] {common_columns_string}", style="green")
    table.add_row("Columns only in:")
    cols_in_a_count = len(cols_only_in_a)
    cols_in_b_count = len(cols_only_in_b)
    cols_in_a_string = _format_list(cols_only_in_a)
    cols_in_b_string = _format_list(cols_only_in_b)
    table.add_row("→ " + result.table_a.name, f"[{cols_in_a_count}] {cols_in_a_string}", style="yellow")
    table.add_row("→ " + result.table_b.name, f"[{cols_in_b_count}] {cols_in_b_string}", style="yellow")
    table.add_row("")

    rows_in_both_diff = result.diff_by_sign.get("!", [])
    rows_only_in_a = result.diff_by_sign.get("-", [])
    rows_only_in_b = result.diff_by_sign.get("+", [])

    table.add_row("Top 5 rows", style="blue")
    table.add_row(
        "Rows in both (diff)", f"[{len(rows_in_both_diff)}] {_format_keys_sample(rows_in_both_diff)}", style="yellow"
    )
    table.add_row("Rows only in:")
    table.add_row(
        "→ " + result.table_a.name, f"[{len(rows_only_in_a)}] {_format_keys_sample(rows_only_in_a)}", style="green"
    )
    table.add_row(
        "→ " + result.table_b.name, f"[{len(rows_only_in_b)}] {_format_keys_sample(rows_only_in_b)}", style="green"
    )

    console.print(Panel.fit(table, padding=(1, 2), title="🕵️‍♀️ Extended info"))
    console.print()


def render_id_samples(result: DiffResult, limit: int = 5) -> None:
    def _render_key(key: object) -> str:
        if isinstance(key, tuple):
            if len(key) == 1:
                return repr(key[0])
            return repr(list(key))
        if isinstance(key, list):
            if len(key) == 1:
                return repr(key[0])
            return repr(key)
        return repr(key)

    def _sql_value(key: object) -> str:
        if isinstance(key, (tuple, list)):
            if len(key) == 1:
                return repr(key[0])
            return "(" + ", ".join(repr(v) for v in key) + ")"
        return repr(key)

    def _build_sql(table_name: str, keys: list[object]) -> Text:
        values = ", ".join(_sql_value(k) for k in keys[:limit])
        text = Text()
        text.append(f"select * from {table_name}\n")
        text.append(f"where {result.primary_key} in ({values})")
        return text

    def _render_panel(title: str, keys: list[object], sql_tables: list[str] | None = None) -> Panel:
        table = Table(show_header=True, box=box.MINIMAL, padding=(0, 2))
        table.add_column(str(result.primary_key), style="bold")
        if not keys:
            table.add_row("No rows")
        else:
            for key in keys[:limit]:
                table.add_row(_render_key(key))

        if keys and sql_tables:
            parts: list[object] = []
            for t in sql_tables:
                parts.append(_build_sql(t, keys))
            parts.append(Text(""))
            parts.append(table)
            return Panel.fit(Group(*parts), padding=(1, 2), title=title)
        return Panel.fit(table, padding=(1, 2), title=title)

    console = Console()
    console.print()

    rows_in_both_diff = result.diff_by_sign.get("!", [])
    rows_only_in_a = result.diff_by_sign.get("-", [])
    rows_only_in_b = result.diff_by_sign.get("+", [])

    console.print(
        _render_panel(f"Rows only in {result.table_a.name} — top {limit}", rows_only_in_a, [result.table_a.name])
    )

    console.print(
        _render_panel(
            f"Rows in both (diff) — top {limit}",
            rows_in_both_diff,
            [result.table_a.name, result.table_b.name],
        )
    )

    console.print(
        _render_panel(f"Rows only in {result.table_b.name} — top {limit}", rows_only_in_b, [result.table_b.name])
    )

    console.print()


def render_schema_diff(result: SchemaDiffResult) -> None:
    """
    Render schema comparison in a table format.

    Args:
        result: SchemaDiffResult containing schema comparison data
    """
    console = Console()
    console.print()

    table = Table(show_header=True, padding=(0, 2), box=box.MINIMAL)
    table.add_column("Column", style="bold")
    table.add_column(result.table_a, justify="left")
    table.add_column(result.table_b, justify="left")
    table.add_column("Status", justify="center")

    for col_name in sorted(result.columns.keys()):
        col_info = result.columns[col_name]
        type_a = col_info["table_a"]
        type_b = col_info["table_b"]

        # Prepare display values
        type_a_display = type_a if type_a is not None else "-"
        type_b_display = type_b if type_b is not None else "-"

        # Determine the status and styling
        if type_a is None:
            status = "+"
            status_style = "green"
        elif type_b is None:
            status = "-"
            status_style = "yellow"
        elif type_a == type_b:
            status = "✓"
            status_style = "green"
        else:
            status = "≠"
            status_style = "yellow"

        table.add_row(col_name, type_a_display, type_b_display, status, style=status_style)

    console.print(Panel.fit(table, padding=(1, 2), title="📋 Schema comparison"))
    console.print()
