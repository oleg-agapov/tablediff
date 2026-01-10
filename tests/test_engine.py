"""
Unit tests for tablediff/engine.py functions.

Tests include:
- get_schema: Verify schema retrieval from DuckDB
- query_table: Verify querying with columns and where clause
- table_diff: Verify DiffResult with added/removed/updated rows
- calculate_differences: Verify diff calculation logic
"""

import pytest
import duckdb
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from tablediff.engine import (
    get_schema,
    query_table,
    table_diff,
    calculate_differences,
)
from tablediff.models import DiffResult, TableMeta


@pytest.fixture
def temp_duckdb(tmp_path):
    """
    Create a temporary DuckDB database with sample tables for testing.
    
    Creates two tables:
    - users_a: with columns (id, name, email, age)
    - users_b: with columns (id, name, email, age)
    
    With sample data to test added, removed, and updated rows.
    """
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    
    # Create table A with initial data
    conn.execute("""
        CREATE TABLE users_a (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            age INTEGER
        )
    """)
    
    conn.execute("""
        INSERT INTO users_a VALUES
        (1, 'Alice', 'alice@example.com', 30),
        (2, 'Bob', 'bob@example.com', 25),
        (3, 'Charlie', 'charlie@example.com', 35),
        (4, 'David', 'david@example.com', 28)
    """)
    
    # Create table B with modified data
    # - Row 1: same as A (unchanged)
    # - Row 2: updated (different email)
    # - Row 3: removed (not in B)
    # - Row 5: added (not in A)
    conn.execute("""
        CREATE TABLE users_b (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            age INTEGER
        )
    """)
    
    conn.execute("""
        INSERT INTO users_b VALUES
        (1, 'Alice', 'alice@example.com', 30),
        (2, 'Bob', 'bob_new@example.com', 25),
        (4, 'David', 'david_new@example.com', 29),
        (5, 'Eve', 'eve@example.com', 27)
    """)
    
    conn.close()
    
    yield str(db_path)
    
    # Cleanup is handled by tmp_path fixture


class TestGetSchema:
    """Tests for get_schema function."""
    
    def test_get_schema_returns_columns(self, temp_duckdb):
        """Test that get_schema returns the correct column names for a table."""
        schema = get_schema(f"duckdb://{temp_duckdb}", "users_a")
        
        # Schema should be a dict-like structure with column names
        assert "id" in schema
        assert "name" in schema
        assert "email" in schema
        assert "age" in schema
    
    def test_get_schema_different_tables(self, temp_duckdb):
        """Test that get_schema works for both tables."""
        schema_a = get_schema(f"duckdb://{temp_duckdb}", "users_a")
        schema_b = get_schema(f"duckdb://{temp_duckdb}", "users_b")
        
        # Both tables should have the same schema
        assert set(schema_a.keys()) == set(schema_b.keys())
    
    def test_get_schema_with_qualified_name(self, temp_duckdb):
        """Test that get_schema handles qualified table names (schema.table)."""
        # For DuckDB, the default schema is 'main'
        schema = get_schema(f"duckdb://{temp_duckdb}", "main.users_a")
        
        assert "id" in schema
        assert "name" in schema


class TestQueryTable:
    """Tests for query_table function."""
    
    def test_query_table_all_columns(self, temp_duckdb):
        """Test querying all columns from a table."""
        columns = ["id", "name", "email", "age"]
        rows = query_table(f"duckdb://{temp_duckdb}", "users_a", columns)
        
        assert len(rows) == 4
        # Check first row
        assert rows[0][0] == 1  # id
        assert rows[0][1] == "Alice"  # name
    
    def test_query_table_specific_columns(self, temp_duckdb):
        """Test querying specific columns from a table."""
        columns = ["id", "name"]
        rows = query_table(f"duckdb://{temp_duckdb}", "users_a", columns)
        
        assert len(rows) == 4
        # Each row should have only 2 columns
        assert len(rows[0]) == 2
    
    def test_query_table_with_where_clause(self, temp_duckdb):
        """Test querying with a WHERE clause."""
        columns = ["id", "name", "age"]
        rows = query_table(
            f"duckdb://{temp_duckdb}",
            "users_a",
            columns,
            where="age > 28"
        )
        
        # Should return 2 rows: Alice (30) and Charlie (35)
        assert len(rows) == 2
    
    def test_query_table_default_where(self, temp_duckdb):
        """Test that default WHERE clause (1 = 1) returns all rows."""
        columns = ["id"]
        rows = query_table(f"duckdb://{temp_duckdb}", "users_a", columns)
        
        assert len(rows) == 4


class TestCalculateDifferences:
    """Tests for calculate_differences function."""
    
    def test_calculate_differences_basic(self):
        """Test calculate_differences with a mock diffing result."""
        # Create a mock DiffResultWrapper
        mock_diffing = MagicMock()
        
        # Mock the info_tree structure
        mock_info = MagicMock()
        mock_info.key_columns = ["id"]
        mock_table_info = MagicMock()
        mock_table_info.key_columns = ["id"]
        mock_info.tables = [mock_table_info]
        mock_diffing.info_tree = MagicMock()
        mock_diffing.info_tree.info = mock_info
        
        # Mock result_list with test data
        # Format: (sign, values)
        # '+' = only in table B (added)
        # '-' = only in table A (removed)
        # '!' = in both but different (updated)
        mock_diffing.result_list = [
            ("+", (5, "Eve", "eve@example.com", 27)),  # Added
            ("-", (3, "Charlie", "charlie@example.com", 35)),  # Removed
            ("-", (2, "Bob", "bob@example.com", 25)),  # First occurrence of updated row
            ("+", (2, "Bob", "bob_new@example.com", 25)),  # Second occurrence (marks as updated)
        ]
        
        diff_by_key, diff_by_sign = calculate_differences(mock_diffing)
        
        # Check diff_by_key
        assert diff_by_key[(5,)] == "+"  # Added
        assert diff_by_key[(3,)] == "-"  # Removed
        assert diff_by_key[(2,)] == "!"  # Updated (both - and + present)
        
        # Check diff_by_sign
        assert (5,) in diff_by_sign["+"]
        assert (3,) in diff_by_sign["-"]
        assert (2,) in diff_by_sign["!"]
    
    def test_calculate_differences_composite_key(self):
        """Test calculate_differences with composite primary key."""
        mock_diffing = MagicMock()
        
        # Mock with composite key
        mock_info = MagicMock()
        mock_info.key_columns = ["id", "type"]
        mock_table_info = MagicMock()
        mock_table_info.key_columns = ["id", "type"]
        mock_info.tables = [mock_table_info]
        mock_diffing.info_tree = MagicMock()
        mock_diffing.info_tree.info = mock_info
        
        mock_diffing.result_list = [
            ("+", (1, "A", "data1")),
            ("-", (2, "B", "data2")),
        ]
        
        diff_by_key, diff_by_sign = calculate_differences(mock_diffing)
        
        # Composite keys should be tuples
        assert diff_by_key[(1, "A")] == "+"
        assert diff_by_key[(2, "B")] == "-"


class TestTableDiff:
    """Tests for table_diff function."""
    
    def test_table_diff_basic(self, temp_duckdb):
        """Test table_diff with two tables having added/removed/updated rows."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "users_a", "users_b", "id")
        
        # Check result type
        assert isinstance(result, DiffResult)
        
        # Check table metadata
        assert result.table_a.name == "users_a"
        assert result.table_b.name == "users_b"
        assert result.primary_key == "id"
        
        # Check column lists
        assert "id" in result.common_columns
        assert "name" in result.common_columns
        assert "email" in result.common_columns
        
        # Check row counts
        assert result.table_a.rows == 4  # users_a has 4 rows
        assert result.table_b.rows == 4  # users_b has 4 rows
        
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
        
        result = table_diff(db_path, "users_a", "users_b", "id")
        
        # All columns should be common since both tables have same schema
        assert set(result.common_columns) == {"id", "name", "email", "age"}
    
    def test_table_diff_diff_by_keys(self, temp_duckdb):
        """Test that diff_by_keys contains the correct mappings."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "users_a", "users_b", "id")
        
        # Check diff_by_keys structure
        # Note: Keys are returned as strings from reladiff
        assert ('3',) in result.diff_by_keys  # Removed row
        assert ('5',) in result.diff_by_keys  # Added row
        assert ('2',) in result.diff_by_keys  # Updated row
        assert ('4',) in result.diff_by_keys  # Updated row
    
    def test_table_diff_diff_by_sign(self, temp_duckdb):
        """Test that diff_by_sign contains the correct groupings."""
        db_path = f"duckdb://{temp_duckdb}"
        
        result = table_diff(db_path, "users_a", "users_b", "id")
        
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
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_table_diff_calls_reladiff_functions(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """Test that table_diff properly calls reladiff functions."""
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "name": "VARCHAR"},  # schema_a
            {"id": "INTEGER", "name": "VARCHAR"},  # schema_b
        ]
        
        mock_table_a = MagicMock()
        mock_table_b = MagicMock()
        mock_connect_to_table.side_effect = [mock_table_a, mock_table_b]
        
        mock_diffing = MagicMock()
        mock_diffing.get_stats_dict.return_value = {
            "rows_A": 10,
            "rows_B": 12,
            "exclusive_A": 2,
            "exclusive_B": 4,
            "unchanged": 6,
            "updated": 2,
        }
        
        # Mock info_tree for calculate_differences
        mock_info = MagicMock()
        mock_table_info = MagicMock()
        mock_table_info.key_columns = ["id"]
        mock_info.tables = [mock_table_info]
        mock_diffing.info_tree = MagicMock()
        mock_diffing.info_tree.info = mock_info
        mock_diffing.result_list = []
        
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        result = table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify reladiff functions were called
        assert mock_connect_to_table.call_count == 2
        mock_connect_to_table.assert_any_call("duckdb://test.db", "table_a", "id")
        mock_connect_to_table.assert_any_call("duckdb://test.db", "table_b", "id")
        
        mock_diff_tables.assert_called_once()
        
        # Verify result
        assert result.table_a.rows == 10
        assert result.table_b.rows == 12
        assert result.rows_only_in_a == 2
        assert result.rows_only_in_b == 4
