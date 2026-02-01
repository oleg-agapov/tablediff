"""
Unit tests for CSV comparison functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from tablediff.engine import load_csv_to_duckdb
from tablediff.cli import main


@pytest.fixture
def csv_files(tmp_path):
    """
    Create temporary CSV files for testing.
    """
    # Create CSV file A
    csv_a = tmp_path / "table_a.csv"
    csv_a.write_text("""id,name,email,age
1,Alice,alice@example.com,30
2,Bob,bob@example.com,25
3,Charlie,charlie@example.com,35
4,David,david@example.com,28
""")
    
    # Create CSV file B with modifications
    csv_b = tmp_path / "table_b.csv"
    csv_b.write_text("""id,name,email,age
1,Alice,alice@example.com,30
2,Bob,bob_new@example.com,25
4,David,david_new@example.com,29
5,Eve,eve@example.com,27
""")
    
    return str(csv_a), str(csv_b)


class TestLoadCSVToDuckDB:
    """Tests for load_csv_to_duckdb function."""
    
    def test_load_csv_creates_tables(self, csv_files):
        """Test that CSV files are loaded into DuckDB tables."""
        csv_a, csv_b = csv_files
        
        conn_str, temp_db_path = load_csv_to_duckdb(csv_a, csv_b)
        
        # Verify connection string format
        assert conn_str.startswith("duckdb://")
        assert temp_db_path in conn_str
        
        # Verify temp database file exists
        assert os.path.exists(temp_db_path)
        
        # Verify tables were created by connecting to the database
        import duckdb
        conn = duckdb.connect(temp_db_path)
        
        # Check table_a
        result_a = conn.execute("SELECT * FROM table_a ORDER BY id").fetchall()
        assert len(result_a) == 4
        assert result_a[0] == (1, 'Alice', 'alice@example.com', 30)
        
        # Check table_b
        result_b = conn.execute("SELECT * FROM table_b ORDER BY id").fetchall()
        assert len(result_b) == 4
        assert result_b[0] == (1, 'Alice', 'alice@example.com', 30)
        assert result_b[1] == (2, 'Bob', 'bob_new@example.com', 25)
        
        conn.close()
        
        # Clean up
        os.unlink(temp_db_path)
    
    def test_load_csv_with_custom_table_names(self, csv_files):
        """Test that custom table names are used."""
        csv_a, csv_b = csv_files
        
        conn_str, temp_db_path = load_csv_to_duckdb(
            csv_a, csv_b, 
            table_name_a="custom_a", 
            table_name_b="custom_b"
        )
        
        import duckdb
        conn = duckdb.connect(temp_db_path)
        
        # Check custom table names exist
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=?", ['main']).fetchall()
        table_names = [t[0] for t in tables]
        
        assert "custom_a" in table_names
        assert "custom_b" in table_names
        
        conn.close()
        os.unlink(temp_db_path)


class TestCSVCLI:
    """Tests for CSV CLI functionality."""
    
    def test_parser_accepts_csv_flag(self):
        """Test that parser accepts --csv argument."""
        from tablediff.cli import build_parser
        
        parser = build_parser()
        args = parser.parse_args([
            "file_a.csv", "file_b.csv",
            "--pk", "id",
            "--csv"
        ])
        
        assert args.csv is True
        assert args.table_a == "file_a.csv"
        assert args.table_b == "file_b.csv"
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    @patch('tablediff.cli.load_csv_to_duckdb')
    def test_main_csv_mode_basic(self, mock_load_csv, mock_render, mock_table_diff, csv_files):
        """Test that main function handles CSV mode correctly."""
        csv_a, csv_b = csv_files
        
        # Mock load_csv_to_duckdb to return a connection string
        mock_load_csv.return_value = ("duckdb:///tmp/test.duckdb", "/tmp/test.duckdb")
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            csv_a, csv_b,
            '--pk', 'id',
            '--csv'
        ]):
            main()
        
        # Verify load_csv_to_duckdb was called with correct paths
        mock_load_csv.assert_called_once_with(
            csv_a,
            csv_b,
            table_name_a="table_a_csv",
            table_name_b="table_b_csv",
        )
        
        # Verify table_diff was called with the temporary database
        mock_table_diff.assert_called_once()
        call_args = mock_table_diff.call_args
        assert call_args[0][0] == "duckdb:///tmp/test.duckdb"  # conn_a
        assert call_args[0][1] == "duckdb:///tmp/test.duckdb"  # conn_b
        assert call_args[0][2] == "table_a_csv"  # table_a_name
        assert call_args[0][3] == "table_b_csv"  # table_b_name
        assert call_args[0][4] == "id"  # primary key
    
    def test_main_csv_mode_file_not_found(self):
        """Test that main function raises error when CSV file not found."""
        with patch('sys.argv', [
            'tablediff',
            '/nonexistent/file_a.csv', '/nonexistent/file_b.csv',
            '--pk', 'id',
            '--csv'
        ]):
            with pytest.raises(SystemExit):
                main()
    
    @patch('tablediff.cli.table_diff')
    @patch('tablediff.cli.render_summary_table')
    @patch('tablediff.cli.load_csv_to_duckdb')
    def test_main_csv_mode_with_where(self, mock_load_csv, mock_render, mock_table_diff, csv_files):
        """Test that CSV mode works with WHERE clause."""
        csv_a, csv_b = csv_files
        
        mock_load_csv.return_value = ("duckdb:///tmp/test.duckdb", "/tmp/test.duckdb")
        mock_table_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            csv_a, csv_b,
            '--pk', 'id',
            '--csv',
            '--where', 'age > 25'
        ]):
            main()
        
        # Verify where clause is passed through
        call_args = mock_table_diff.call_args
        assert call_args[1]['where'] == 'age > 25'
    
    @patch('tablediff.cli.schema_diff')
    @patch('tablediff.cli.render_schema_diff')
    @patch('tablediff.cli.load_csv_to_duckdb')
    def test_main_csv_mode_schema_only(self, mock_load_csv, mock_render, mock_schema_diff, csv_files):
        """Test that CSV mode works with --schema-only flag."""
        csv_a, csv_b = csv_files
        
        mock_load_csv.return_value = ("duckdb:///tmp/test.duckdb", "/tmp/test.duckdb")
        mock_schema_diff.return_value = MagicMock()
        
        with patch('sys.argv', [
            'tablediff',
            csv_a, csv_b,
            '--csv',
            '--schema-only'
        ]):
            main()
        
        # Verify schema_diff was called
        mock_schema_diff.assert_called_once_with(
            "duckdb:///tmp/test.duckdb",
            "duckdb:///tmp/test.duckdb",
            "table_a_csv",
            "table_b_csv"
        )


class TestCSVIntegration:
    """Integration tests for CSV comparison."""
    
    def test_csv_comparison_end_to_end(self, csv_files):
        """Test end-to-end CSV comparison without mocking."""
        csv_a, csv_b = csv_files
        
        with patch('sys.argv', [
            'tablediff',
            csv_a, csv_b,
            '--pk', 'id',
            '--csv'
        ]):
            # This should not raise an error
            main()
