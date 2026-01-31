"""
Unit tests for tablediff CLI functionality.

Tests the CLI argument parsing and connection string handling for:
- Single connection (--conn)
- Cross-database connections (--conn-a and --conn-b)
- Mixed usage (--conn with --conn-a/--conn-b overrides)
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
        assert args.conn_a is None
        assert args.conn_b is None
    
    def test_parser_accepts_conn_a_and_conn_b(self):
        """Test that parser accepts --conn-a and --conn-b arguments."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--pk", "id",
            "--conn-a", "duckdb://./db_a.duckdb",
            "--conn-b", "duckdb://./db_b.duckdb"
        ])
        
        assert args.conn_a == "duckdb://./db_a.duckdb"
        assert args.conn_b == "duckdb://./db_b.duckdb"
        assert args.conn is None
    
    def test_parser_accepts_mixed_conn_arguments(self):
        """Test that parser accepts --conn with --conn-a/--conn-b overrides."""
        parser = build_parser()
        args = parser.parse_args([
            "table_a", "table_b",
            "--pk", "id",
            "--conn", "duckdb://./default.duckdb",
            "--conn-a", "duckdb://./db_a.duckdb"
        ])
        
        assert args.conn == "duckdb://./default.duckdb"
        assert args.conn_a == "duckdb://./db_a.duckdb"
        assert args.conn_b is None


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
        """Test that main uses --conn-a and --conn-b when both are provided."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn-a', 'duckdb://./db_a.duckdb',
            '--conn-b', 'duckdb://./db_b.duckdb'
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
    def test_main_conn_a_overrides_conn_for_table_a(self, mock_render, mock_table_diff):
        """Test that --conn-a overrides --conn for table_a."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./default.duckdb',
            '--conn-a', 'duckdb://./db_a.duckdb'
        ]):
            main()
        
        # Verify conn_a uses --conn-a, conn_b uses --conn
        mock_table_diff.assert_called_once_with(
            'duckdb://./db_a.duckdb',     # conn_a (overridden)
            'duckdb://./default.duckdb',  # conn_b (default)
            'table_a',
            'table_b',
            'id',
            where=None
        )
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_conn_b_overrides_conn_for_table_b(self, mock_render, mock_table_diff):
        """Test that --conn-b overrides --conn for table_b."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./default.duckdb',
            '--conn-b', 'duckdb://./db_b.duckdb'
        ]):
            main()
        
        # Verify conn_a uses --conn, conn_b uses --conn-b
        mock_table_diff.assert_called_once_with(
            'duckdb://./default.duckdb',  # conn_a (default)
            'duckdb://./db_b.duckdb',     # conn_b (overridden)
            'table_a',
            'table_b',
            'id',
            where=None
        )
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_both_overrides_with_conn(self, mock_render, mock_table_diff):
        """Test that both --conn-a and --conn-b override --conn."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn', 'duckdb://./default.duckdb',
            '--conn-a', 'duckdb://./db_a.duckdb',
            '--conn-b', 'duckdb://./db_b.duckdb'
        ]):
            main()
        
        # Verify both connections are overridden
        mock_table_diff.assert_called_once_with(
            'duckdb://./db_a.duckdb',  # conn_a (overridden)
            'duckdb://./db_b.duckdb',  # conn_b (overridden)
            'table_a',
            'table_b',
            'id',
            where=None
        )
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    @patch('tablediff.cli.render_extended_table')
    def test_main_extended_flag_works_with_cross_db(self, mock_ext, mock_summary, mock_table_diff):
        """Test that --extended flag works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn-a', 'duckdb://./db_a.duckdb',
            '--conn-b', 'duckdb://./db_b.duckdb',
            '--extended'
        ]):
            main()
        
        # Verify extended output is rendered
        mock_summary.assert_called_once()
        mock_ext.assert_called_once()
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    def test_main_where_clause_works_with_cross_db(self, mock_render, mock_table_diff):
        """Test that --where clause works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            'table_a', 'table_b',
            '--pk', 'id',
            '--conn-a', 'duckdb://./db_a.duckdb',
            '--conn-b', 'duckdb://./db_b.duckdb',
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
