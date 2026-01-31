"""
Unit tests for tablediff CLI functionality.

Tests the CLI argument parsing and connection string handling for:
- Single connection (--conn)
- Cross-database connections (--conn and --conn2)
"""

import pytest
from unittest.mock import patch, MagicMock
from tablediff.cli import build_parser, main


class TestCLIArguments:
    """Tests for CLI argument parsing."""
    
    def test_parser_accepts_conn_only(self):
        """Test that parser accepts --conn argument."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--pk", "id",
            "--conn", "duckdb://./db.duckdb"
        ])
        
        assert args.conn == "duckdb://./db.duckdb"
        assert args.conn2 is None
    
    def test_parser_accepts_conn_and_conn2(self):
        """Test that parser accepts --conn and --conn2 arguments."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--pk", "id",
            "--conn", "duckdb://./db_a.duckdb",
            "--conn2", "duckdb://./db_b.duckdb"
        ])
        
        assert args.conn == "duckdb://./db_a.duckdb"
        assert args.conn2 == "duckdb://./db_b.duckdb"
    
    def test_parser_accepts_schema_only(self):
        """Test that parser accepts --schema-only argument."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--conn", "duckdb://./db.duckdb",
            "--schema-only"
        ])
        
        assert args.schema_only is True
    
    def test_parser_schema_only_without_pk(self):
        """Test that parser accepts --schema-only without --pk."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--conn", "duckdb://./db.duckdb",
            "--schema-only"
        ])
        
        # Should not raise an error
        assert args.schema_only is True
        assert args.pk is None


class TestCLIConnectionLogic:
    """Tests for connection string resolution logic in main()."""
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_uses_conn_for_both_tables(self, mock_render, mock_table_diff):
        """Test that main uses --conn for both tables when only --conn is provided."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./db.duckdb'
        ]):
            main()
        
        # Verify table_diff was called with the same connection for both tables
        mock_table_diff.assert_called_once_with(
            'duckdb://./db.duckdb',  # conn_a
            'duckdb://./db.duckdb',  # conn_b
            'table_a',
            'table_b',
            'id',
            where=None
        )
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_uses_separate_connections(self, mock_render, mock_table_diff):
        """Test that main uses --conn and --conn2 when both are provided."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./db_a.duckdb',
            '--conn2', 'duckdb://./db_b.duckdb'
        ]):
            main()
        
        # Verify table_diff was called with different connections
        mock_table_diff.assert_called_once_with(
            'duckdb://./db_a.duckdb',  # conn_a
            'duckdb://./db_b.duckdb',  # conn_b
            'table_a',
            'table_b',
            'id',
            where=None
        )
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    @patch('tablediff.cli.render_extended_table')
    @patch('tablediff.cli.schema_diff')
    @patch('tablediff.cli.render_schema_diff')
    def test_main_extended_flag_works_with_cross_db(self, mock_schema_render, mock_schema_diff, mock_ext, mock_summary, mock_table_diff):
        """Test that --extended flag works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()
        mock_schema_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./db_a.duckdb',
            '--conn2', 'duckdb://./db_b.duckdb',
            '--extended'
        ]):
            main()
        
        # Verify extended output is rendered
        mock_summary.assert_called_once()
        mock_ext.assert_called_once()
        # Verify schema comparison is also rendered in extended mode
        mock_schema_diff.assert_called_once()
        mock_schema_render.assert_called_once()
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_where_clause_works_with_cross_db(self, mock_render, mock_table_diff):
        """Test that --where clause works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./db_a.duckdb',
            '--conn2', 'duckdb://./db_b.duckdb',
            '--where', 'status = "active"'
        ]):
            main()
        
        # Verify where clause is passed through
        mock_table_diff.assert_called_once_with(
            'duckdb://./db_a.duckdb',
            'duckdb://./db_b.duckdb',
            'table_a',
            'table_b',
            'id',
            where='status = "active"'
        )
    
    @patch('tablediff.cli.schema_diff')
    @patch('tablediff.cli.render_schema_diff')
    def test_main_schema_only_flag(self, mock_render, mock_schema_diff):
        """Test that --schema-only flag calls schema_diff instead of table_diff."""
        mock_schema_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--conn', 'duckdb://./db.duckdb',
            '--schema-only'
        ]):
            main()
        
        # Verify schema_diff was called
        mock_schema_diff.assert_called_once_with(
            'duckdb://./db.duckdb',
            'duckdb://./db.duckdb',
            'table_a',
            'table_b'
        )
        mock_render.assert_called_once()
    
    @patch('tablediff.cli.schema_diff')
    @patch('tablediff.cli.render_schema_diff')
    def test_main_schema_only_with_cross_db(self, mock_render, mock_schema_diff):
        """Test that --schema-only works with cross-database comparison."""
        mock_schema_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--conn', 'duckdb://./db_a.duckdb',
            '--conn2', 'duckdb://./db_b.duckdb',
            '--schema-only'
        ]):
            main()
        
        # Verify schema_diff was called with different connections
        mock_schema_diff.assert_called_once_with(
            'duckdb://./db_a.duckdb',
            'duckdb://./db_b.duckdb',
            'table_a',
            'table_b'
        )
        mock_render.assert_called_once()
