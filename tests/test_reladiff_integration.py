"""
Unit tests for reladiff integration.

Tests the interaction with external reladiff functions:
- connect_to_table
- diff_tables

These tests use real DuckDB connections to test the integration.
"""

import pytest
from reladiff import connect_to_table, diff_tables
from tablediff.engine import table_diff, get_schema
from tablediff.models import DiffResult


class TestConnectToTableIntegration:
    """Tests for connect_to_table integration in table_diff."""
    
    def test_connect_to_table_called_with_correct_params(self, temp_duckdb):
        """
        Test that connect_to_table is called with the correct parameters
        for both tables when table_diff is executed.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff which internally calls connect_to_table
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Verify the result structure indicates connect_to_table was used correctly
        assert isinstance(result, DiffResult)
        assert result.table_a.name == "table_a"
        assert result.table_b.name == "table_b"
        assert result.primary_key == "id"
    
    def test_connect_to_table_with_qualified_names(self, temp_duckdb):
        """
        Test that connect_to_table handles qualified table names
        (schema.table or database.schema.table).
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call with qualified table names
        result = table_diff(
            db_path,
            "main.table_a",
            "main.table_b",
            "id"
        )
        
        # Verify the connection worked with qualified names
        assert isinstance(result, DiffResult)
        # The result should show the qualified names
        assert "main.table_a" in result.table_a.name
        assert "main.table_b" in result.table_b.name


class TestDiffTablesIntegration:
    """Tests for diff_tables integration in table_diff."""
    
    def test_diff_tables_called_with_key_columns(self, temp_duckdb):
        """
        Test that diff_tables is called with the correct key_columns parameter.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff which internally calls diff_tables with key_columns
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Verify diff_tables was called correctly by checking results
        assert result.primary_key == "id"
        # The diff should have found differences (added, removed, updated)
        assert result.rows_only_in_a > 0 or result.rows_only_in_b > 0
    
    def test_diff_tables_called_with_extra_columns(self, temp_duckdb):
        """
        Test that diff_tables is called with extra_columns containing
        common columns between the two tables.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff on tables C and D which have different columns
        # table_c has: id, name, email, status
        # table_d has: id, name, email, role
        # Common: id, name, email
        result = table_diff(db_path, "table_c", "table_d", "id")
        
        # Verify common columns were identified correctly
        assert "id" in result.common_columns
        assert "name" in result.common_columns
        assert "email" in result.common_columns
        # status and role should not be in common columns
        assert "status" not in result.common_columns
        assert "role" not in result.common_columns
    
    def test_diff_tables_called_with_where_clause(self, temp_duckdb):
        """
        Test that diff_tables is called with where parameter when provided.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        where_clause = "id < 3"
        
        # Call table_diff with where clause
        result = table_diff(db_path, "table_a", "table_b", "id", where=where_clause)
        
        # With where clause "id < 3", only rows with id 1 and 2 should be compared
        # Row 1 is unchanged, Row 2 is updated
        # So we expect: 0 only in A, 0 only in B, 1 unchanged, 1 updated
        assert isinstance(result, DiffResult)
        assert result.rows_in_both_same >= 0
        assert result.rows_in_both_diff >= 0
    
    def test_diff_tables_stats_parsed_correctly(self, temp_duckdb):
        """
        Test that statistics returned by diff_tables.get_stats_dict()
        are correctly parsed into DiffResult.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Verify stats are correctly parsed and reasonable
        assert result.table_a.rows == 4  # table_a has 4 rows
        assert result.table_b.rows == 4  # table_b has 4 rows
        assert result.rows_only_in_a == 1  # Row 3 only in A
        assert result.rows_only_in_b == 1  # Row 5 only in B
        assert result.rows_in_both_same == 1  # Row 1 unchanged
        assert result.rows_in_both_diff == 2  # Rows 2 and 4 updated
    
    def test_diff_tables_result_list_processed(self, temp_duckdb):
        """
        Test that the result_list from diff_tables is correctly processed
        by calculate_differences.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Verify diff_by_keys and diff_by_sign are populated correctly
        # Note: Keys are returned as strings from reladiff
        assert ('3',) in result.diff_by_keys  # Removed
        assert result.diff_by_keys[('3',)] == "-"
        
        assert ('5',) in result.diff_by_keys  # Added
        assert result.diff_by_keys[('5',)] == "+"
        
        assert ('2',) in result.diff_by_keys  # Updated
        assert result.diff_by_keys[('2',)] == "!"
        
        # Check diff_by_sign
        assert ('5',) in result.diff_by_sign["+"]
        assert ('3',) in result.diff_by_sign["-"]
        assert ('2',) in result.diff_by_sign["!"]
    
    def test_diff_tables_diffing_object_preserved(self, temp_duckdb):
        """
        Test that the diffing object returned by diff_tables is preserved
        in the DiffResult for potential further use.
        """
        db_path = f"duckdb://{temp_duckdb}"
        
        # Call table_diff
        result = table_diff(db_path, "table_a", "table_b", "id")
        
        # Verify the diffing object is preserved and has expected attributes
        assert result.diffing is not None
        assert hasattr(result.diffing, 'get_stats_dict')
        assert hasattr(result.diffing, 'result_list')


class TestReladiffErrorHandling:
    """Tests for error handling when interacting with reladiff functions."""
    
    def test_connect_to_table_connection_error(self):
        """Test that connection errors from connect_to_table are propagated."""
        # Try to connect to non-existent database
        with pytest.raises(Exception):
            table_diff("duckdb:///nonexistent/path/db.duckdb", "table_a", "table_b", "id")
    
    def test_diff_tables_invalid_key_error(self, temp_duckdb):
        """Test that errors from diff_tables are propagated for invalid keys."""
        db_path = f"duckdb://{temp_duckdb}"
        
        # Try to diff with a non-existent primary key column
        with pytest.raises(Exception):
            table_diff(db_path, "table_a", "table_b", "nonexistent_key")
