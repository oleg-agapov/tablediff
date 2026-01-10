"""
Unit tests for tablediff/engine.py functions.

Tests include:
- get_schema: Verify schema retrieval from DuckDB
- query_table: Verify querying with columns and where clause
- table_diff: Verify DiffResult with added/removed/updated rows
- calculate_differences: Verify diff calculation logic
"""

import pytest
from reladiff import connect_to_table, diff_tables
from tablediff.engine import (
    get_schema,
    query_table,
    table_diff,
    calculate_differences,
)
from tablediff.models import DiffResult, TableMeta


class TestGetSchema:
    """Tests for get_schema function."""
    
    def test_get_schema_returns_columns(self, temp_duckdb):
        """Test that get_schema returns the correct column names for a table."""
        schema = get_schema(f"duckdb://{temp_duckdb}", "table_a")
        
        # Schema should be a dict-like structure with column names
        assert "id" in schema
        assert "name" in schema
        assert "email" in schema
        assert "age" in schema
    
    def test_get_schema_different_tables(self, temp_duckdb):
        """Test that get_schema works for both tables."""
        schema_a = get_schema(f"duckdb://{temp_duckdb}", "table_a")
        schema_b = get_schema(f"duckdb://{temp_duckdb}", "table_b")
        
        # Both tables should have the same schema
        assert set(schema_a.keys()) == set(schema_b.keys())
    
    def test_get_schema_with_qualified_name(self, temp_duckdb):
        """Test that get_schema handles qualified table names (schema.table)."""
        # For DuckDB, the default schema is 'main'
        schema = get_schema(f"duckdb://{temp_duckdb}", "main.table_a")
        
        assert "id" in schema
        assert "name" in schema


class TestQueryTable:
    """Tests for query_table function."""
    
    def test_query_table_all_columns(self, temp_duckdb):
        """Test querying all columns from a table."""
        columns = ["id", "name", "email", "age"]
        rows = query_table(f"duckdb://{temp_duckdb}", "table_a", columns)
        
        assert len(rows) == 4
        # Check first row
        assert rows[0][0] == 1  # id
        assert rows[0][1] == "Alice"  # name
    
    def test_query_table_specific_columns(self, temp_duckdb):
        """Test querying specific columns from a table."""
        columns = ["id", "name"]
        rows = query_table(f"duckdb://{temp_duckdb}", "table_a", columns)
        
        assert len(rows) == 4
        # Each row should have only 2 columns
        assert len(rows[0]) == 2
    
    def test_query_table_with_where_clause(self, temp_duckdb):
        """Test querying with a WHERE clause."""
        columns = ["id", "name", "age"]
        rows = query_table(
            f"duckdb://{temp_duckdb}",
            "table_a",
            columns,
            where="age > 28"
        )
        
        # Should return 2 rows: Alice (30) and Charlie (35)
        assert len(rows) == 2


class TestCalculateDifferences:
    """Tests for calculate_differences function."""
    
    def test_calculate_differences_basic(self, temp_duckdb):
        """Test calculate_differences with real output from diff_tables."""
        db_path = f"duckdb://{temp_duckdb}"
        
        # Create real table segments and diff them
        table_a = connect_to_table(db_path, "table_a", "id")
        table_b = connect_to_table(db_path, "table_b", "id")
        
        # Get common columns
        schema_a = get_schema(db_path, "table_a")
        schema_b = get_schema(db_path, "table_b")
        cols_a = [x for x in schema_a]
        cols_b = [x for x in schema_b]
        common_cols_set = set(cols_a).intersection(cols_b)
        common_cols = [col for col in cols_b if col in common_cols_set]
        
        # Perform the actual diff
        diffing = diff_tables(table_a, table_b, key_columns=tuple(["id"]), extra_columns=tuple(common_cols))
        
        # Calculate differences
        diff_by_key, diff_by_sign = calculate_differences(diffing)
        
        # Check diff_by_key structure
        # Note: Keys are returned as strings from reladiff
        assert ('5',) in diff_by_key  # Added
        assert ('3',) in diff_by_key  # Removed
        assert ('2',) in diff_by_key  # Updated
        assert ('4',) in diff_by_key  # Updated
        
        # Check diff_by_sign
        assert ('5',) in diff_by_sign["+"]  # Added
        assert ('3',) in diff_by_sign["-"]  # Removed
        assert ('2',) in diff_by_sign["!"]  # Updated
        assert ('4',) in diff_by_sign["!"]  # Updated


class TestTableDiff:
    """Tests for table_diff function."""
    
    def test_table_diff_basic(self, temp_duckdb):
        """Test table_diff with two tables having added/removed/updated rows."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Check result type
        assert isinstance(result, DiffResult)
        
        # Check table metadata
        assert result.table_a.name == "table_a"
        assert result.table_b.name == "table_b"
        assert result.primary_key == "id"
        
        # Check column lists
        assert "id" in result.common_columns
        assert "name" in result.common_columns
        assert "email" in result.common_columns
        
        # Check row counts
        assert result.table_a.rows == 4  # table_a has 4 rows
        assert result.table_b.rows == 4  # table_b has 4 rows
        
        # Check diff statistics
        # Row 3 is only in A (removed)
        assert result.rows_only_in_a == 1
        
        # Row 5 is only in B (added)
        assert result.rows_only_in_b == 1
        
        # Row 1 is unchanged
        assert result.rows_in_both_same == 1
        
        # Rows 2 and 4 are updated (different email/age)
        assert result.rows_in_both_diff == 2
    
    def test_table_diff_common_columns(self, temp_duckdb):
        """Test that table_diff correctly identifies common columns."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # All columns should be common since both tables have same schema
        assert set(result.common_columns) == {"id", "name", "email", "age"}
    
    def test_table_diff_diff_by_keys(self, temp_duckdb):
        """Test that diff_by_keys contains the correct mappings."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Check diff_by_keys structure
        # Note: Keys are returned as strings from reladiff
        assert ('3',) in result.diff_by_keys  # Removed row
        assert ('5',) in result.diff_by_keys  # Added row
        assert ('2',) in result.diff_by_keys  # Updated row
        assert ('4',) in result.diff_by_keys  # Updated row
    
    def test_table_diff_diff_by_sign(self, temp_duckdb):
        """Test that diff_by_sign contains the correct groupings."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Check diff_by_sign structure
        assert "-" in result.diff_by_sign
        assert "+" in result.diff_by_sign
        assert "!" in result.diff_by_sign
        
        # Row 3 should be in removed (-)
        # Note: Keys are returned as strings from reladiff
        assert ('3',) in result.diff_by_sign["-"]
        
        # Row 5 should be in added (+)
        assert ('5',) in result.diff_by_sign["+"]
        
        # Rows 2 and 4 should be in updated (!)
        assert ('2',) in result.diff_by_sign["!"]
        assert ('4',) in result.diff_by_sign["!"]
