from __future__ import annotations

from tablediff.adapters.duckdb import DuckDBAdapter


class DefaultAdapter(DuckDBAdapter):
    """Default adapter for tablediff, currently backed by DuckDB."""
