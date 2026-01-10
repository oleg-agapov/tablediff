"""
Unit tests for reladiff integration.

Tests the interaction with external reladiff functions:
- connect_to_table
- diff_tables

These tests use mocking to simulate reladiff behavior without
requiring actual database connections or network access.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from tablediff.engine import table_diff
from tablediff.models import DiffResult


class TestConnectToTableIntegration:
    """Tests for connect_to_table integration in table_diff."""
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_connect_to_table_called_with_correct_params(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that connect_to_table is called with the correct parameters
        for both tables when table_diff is executed.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "name": "VARCHAR", "email": "VARCHAR"},
            {"id": "INTEGER", "name": "VARCHAR", "email": "VARCHAR"},
        ]
        
        mock_table_a = MagicMock()
        mock_table_b = MagicMock()
        mock_connect_to_table.side_effect = [mock_table_a, mock_table_b]
        
        # Setup diff_tables mock
        mock_diffing = self._create_mock_diffing(
            rows_a=10, rows_b=10, exclusive_a=0, exclusive_b=0, 
            unchanged=10, updated=0
        )
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        db_path = "duckdb://test.db"
        table_a_name = "users_a"
        table_b_name = "users_b"
        primary_key = "user_id"
        
        result = table_diff(db_path, table_a_name, table_b_name, primary_key)
        
        # Verify connect_to_table was called twice with correct parameters
        assert mock_connect_to_table.call_count == 2
        
        # Check first call (table A)
        first_call = mock_connect_to_table.call_args_list[0]
        assert first_call[0][0] == db_path
        assert first_call[0][1] == table_a_name
        assert first_call[0][2] == primary_key
        
        # Check second call (table B)
        second_call = mock_connect_to_table.call_args_list[1]
        assert second_call[0][0] == db_path
        assert second_call[0][1] == table_b_name
        assert second_call[0][2] == primary_key
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_connect_to_table_with_qualified_names(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that connect_to_table handles qualified table names
        (schema.table or database.schema.table).
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "data": "VARCHAR"},
            {"id": "INTEGER", "data": "VARCHAR"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        mock_diffing = self._create_mock_diffing(
            rows_a=5, rows_b=5, exclusive_a=0, exclusive_b=0,
            unchanged=5, updated=0
        )
        mock_diff_tables.return_value = mock_diffing
        
        # Call with qualified table names
        table_diff(
            "duckdb://test.db",
            "main.users_a",
            "main.users_b",
            "id"
        )
        
        # Verify connect_to_table received qualified names
        calls = mock_connect_to_table.call_args_list
        assert calls[0][0][1] == "main.users_a"
        assert calls[1][0][1] == "main.users_b"
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_connect_to_table_return_values_passed_to_diff_tables(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that the TableSegment objects returned by connect_to_table
        are passed to diff_tables.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER"},
            {"id": "INTEGER"},
        ]
        
        mock_table_a = MagicMock(name="TableSegment_A")
        mock_table_b = MagicMock(name="TableSegment_B")
        mock_connect_to_table.side_effect = [mock_table_a, mock_table_b]
        
        mock_diffing = self._create_mock_diffing(
            rows_a=1, rows_b=1, exclusive_a=0, exclusive_b=0,
            unchanged=1, updated=0
        )
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify diff_tables was called with the mocked TableSegments
        mock_diff_tables.assert_called_once()
        call_args = mock_diff_tables.call_args
        
        # First two positional arguments should be our mocked tables
        assert call_args[0][0] == mock_table_a
        assert call_args[0][1] == mock_table_b
    
    def _create_mock_diffing(self, rows_a, rows_b, exclusive_a, exclusive_b, 
                            unchanged, updated, result_list=None):
        """Helper to create a mock diffing result."""
        mock_diffing = MagicMock()
        mock_diffing.get_stats_dict.return_value = {
            "rows_A": rows_a,
            "rows_B": rows_b,
            "exclusive_A": exclusive_a,
            "exclusive_B": exclusive_b,
            "unchanged": unchanged,
            "updated": updated,
        }
        
        # Mock info_tree for calculate_differences
        mock_info = MagicMock()
        mock_table_info = MagicMock()
        mock_table_info.key_columns = ["id"]
        mock_info.tables = [mock_table_info]
        mock_diffing.info_tree = MagicMock()
        mock_diffing.info_tree.info = mock_info
        mock_diffing.result_list = result_list if result_list is not None else []
        
        return mock_diffing


class TestDiffTablesIntegration:
    """Tests for diff_tables integration in table_diff."""
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_called_with_key_columns(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that diff_tables is called with the correct key_columns parameter.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "name": "VARCHAR"},
            {"id": "INTEGER", "name": "VARCHAR"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        mock_diffing = self._create_mock_diffing()
        mock_diff_tables.return_value = mock_diffing
        
        primary_key = "user_id"
        
        # Call table_diff
        table_diff("duckdb://test.db", "table_a", "table_b", primary_key)
        
        # Verify diff_tables was called with key_columns as tuple
        mock_diff_tables.assert_called_once()
        call_kwargs = mock_diff_tables.call_args[1]
        assert call_kwargs["key_columns"] == (primary_key,)
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_called_with_extra_columns(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that diff_tables is called with extra_columns containing
        common columns between the two tables.
        """
        # Setup mocks - tables with some common and some unique columns
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "name": "VARCHAR", "email": "VARCHAR", "age": "INTEGER"},
            {"id": "INTEGER", "name": "VARCHAR", "email": "VARCHAR", "status": "VARCHAR"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        mock_diffing = self._create_mock_diffing()
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify diff_tables was called with common columns
        call_kwargs = mock_diff_tables.call_args[1]
        extra_columns = call_kwargs["extra_columns"]
        
        # Common columns should be id, name, email (not age or status)
        assert set(extra_columns) == {"id", "name", "email"}
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_called_with_where_clause(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that diff_tables is called with where parameter when provided.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "status": "VARCHAR"},
            {"id": "INTEGER", "status": "VARCHAR"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        mock_diffing = self._create_mock_diffing()
        mock_diff_tables.return_value = mock_diffing
        
        where_clause = "status = 'active'"
        
        # Call table_diff with where clause
        table_diff("duckdb://test.db", "table_a", "table_b", "id", where=where_clause)
        
        # Verify diff_tables received the where clause
        call_kwargs = mock_diff_tables.call_args[1]
        assert call_kwargs["where"] == where_clause
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_stats_parsed_correctly(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that statistics returned by diff_tables.get_stats_dict()
        are correctly parsed into DiffResult.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER", "data": "VARCHAR"},
            {"id": "INTEGER", "data": "VARCHAR"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        # Create diffing result with specific stats
        mock_diffing = self._create_mock_diffing(
            rows_a=100,
            rows_b=120,
            exclusive_a=15,
            exclusive_b=35,
            unchanged=75,
            updated=10,
        )
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        result = table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify stats are correctly parsed
        assert result.table_a.rows == 100
        assert result.table_b.rows == 120
        assert result.rows_only_in_a == 15
        assert result.rows_only_in_b == 35
        assert result.rows_in_both_same == 75
        assert result.rows_in_both_diff == 10
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_result_list_processed(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that the result_list from diff_tables is correctly processed
        by calculate_differences.
        """
        # Setup mocks
        mock_get_schema.side_effect = [
            {"id": "INTEGER"},
            {"id": "INTEGER"},
        ]
        
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        # Create diffing result with result_list
        result_list = [
            ("+", (10, "data10")),  # Added
            ("-", (20, "data20")),  # Removed
            ("-", (30, "data30")),  # Updated (first part)
            ("+", (30, "data30_new")),  # Updated (second part)
        ]
        
        mock_diffing = self._create_mock_diffing(
            rows_a=3, rows_b=3, exclusive_a=1, exclusive_b=1,
            unchanged=1, updated=1, result_list=result_list
        )
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        result = table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify diff_by_keys and diff_by_sign are populated
        assert (10,) in result.diff_by_keys
        assert result.diff_by_keys[(10,)] == "+"
        
        assert (20,) in result.diff_by_keys
        assert result.diff_by_keys[(20,)] == "-"
        
        assert (30,) in result.diff_by_keys
        assert result.diff_by_keys[(30,)] == "!"  # Updated
        
        # Check diff_by_sign
        assert (10,) in result.diff_by_sign["+"]
        assert (20,) in result.diff_by_sign["-"]
        assert (30,) in result.diff_by_sign["!"]
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_diffing_object_preserved(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """
        Test that the diffing object returned by diff_tables is preserved
        in the DiffResult for potential further use.
        """
        # Setup mocks
        mock_get_schema.side_effect = [{"id": "INTEGER"}, {"id": "INTEGER"}]
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        mock_diffing = self._create_mock_diffing()
        mock_diff_tables.return_value = mock_diffing
        
        # Call table_diff
        result = table_diff("duckdb://test.db", "table_a", "table_b", "id")
        
        # Verify the diffing object is preserved in the result
        assert result.diffing is mock_diffing
    
    def _create_mock_diffing(self, rows_a=10, rows_b=10, exclusive_a=0, 
                            exclusive_b=0, unchanged=10, updated=0, 
                            result_list=None):
        """Helper to create a mock diffing result."""
        mock_diffing = MagicMock()
        mock_diffing.get_stats_dict.return_value = {
            "rows_A": rows_a,
            "rows_B": rows_b,
            "exclusive_A": exclusive_a,
            "exclusive_B": exclusive_b,
            "unchanged": unchanged,
            "updated": updated,
        }
        
        # Mock info_tree for calculate_differences
        mock_info = MagicMock()
        mock_table_info = MagicMock()
        mock_table_info.key_columns = ["id"]
        mock_info.tables = [mock_table_info]
        mock_diffing.info_tree = MagicMock()
        mock_diffing.info_tree.info = mock_info
        mock_diffing.result_list = result_list if result_list is not None else []
        
        return mock_diffing


class TestReladiffErrorHandling:
    """Tests for error handling when interacting with reladiff functions."""
    
    @patch("tablediff.engine.connect_to_table")
    def test_connect_to_table_connection_error(self, mock_connect_to_table):
        """Test that connection errors from connect_to_table are propagated."""
        # Simulate connection error
        mock_connect_to_table.side_effect = Exception("Connection failed")
        
        # Should raise the exception
        with pytest.raises(Exception, match="Connection failed"):
            table_diff("duckdb://test.db", "table_a", "table_b", "id")
    
    @patch("tablediff.engine.connect_to_table")
    @patch("tablediff.engine.diff_tables")
    @patch("tablediff.engine.get_schema")
    def test_diff_tables_invalid_key_error(
        self, mock_get_schema, mock_diff_tables, mock_connect_to_table
    ):
        """Test that errors from diff_tables are propagated."""
        # Setup mocks
        mock_get_schema.side_effect = [{"id": "INTEGER"}, {"id": "INTEGER"}]
        mock_connect_to_table.side_effect = [MagicMock(), MagicMock()]
        
        # Simulate error from diff_tables
        mock_diff_tables.side_effect = ValueError("Invalid primary key")
        
        # Should raise the exception
        with pytest.raises(ValueError, match="Invalid primary key"):
            table_diff("duckdb://test.db", "table_a", "table_b", "invalid_key")
