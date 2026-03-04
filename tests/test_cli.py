"""
Unit tests for tablediff CLI functionality.

Tests the CLI argument parsing and connection string handling for:
- Single connection (--conn)
- Cross-database connections (--conn and --conn2)
"""

from unittest.mock import MagicMock, patch

from tablediff.cli import build_parser, main


class TestCLIArguments:
    """Tests for CLI argument parsing."""

    def test_parser_accepts_conn_only(self):
        """Test that parser accepts --conn argument."""
        parser = build_parser()
        args = parser.parse_args(["compare", "table_a", "table_b", "--pk", "id", "--conn", "duckdb://./db.duckdb"])

        assert args.command == "compare"
        assert args.conn == "duckdb://./db.duckdb"
        assert args.conn2 is None

    def test_parser_accepts_conn_and_conn2(self):
        """Test that parser accepts --conn and --conn2 arguments."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "table_a",
                "table_b",
                "--pk",
                "id",
                "--conn",
                "duckdb://./db_a.duckdb",
                "--conn2",
                "duckdb://./db_b.duckdb",
            ]
        )

        assert args.command == "compare"
        assert args.conn == "duckdb://./db_a.duckdb"
        assert args.conn2 == "duckdb://./db_b.duckdb"

    def test_parser_accepts_schema_command(self):
        """Test that parser accepts schema command."""
        parser = build_parser()
        args = parser.parse_args(["schema", "table_a", "table_b", "--conn", "duckdb://./db.duckdb"])

        assert args.command == "schema"


class TestCLIConnectionLogic:
    """Tests for connection string resolution logic in main()."""

    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_uses_conn_for_both_tables(self, mock_render, mock_table_diff):
        """Test that main uses --conn for both tables when only --conn is provided."""
        mock_table_diff.return_value = MagicMock()

        with patch(
            "sys.argv", ["tablediff", "compare", "table_a", "table_b", "--pk", "id", "--conn", "duckdb://./db.duckdb"]
        ):
            main()

        # Verify table_diff was called with the same connection for both tables
        mock_table_diff.assert_called_once_with(
            "duckdb://./db.duckdb",  # conn_a
            "duckdb://./db.duckdb",  # conn_b
            "table_a",
            "table_b",
            "id",
            where=None,
        )

    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_uses_separate_connections(self, mock_render, mock_table_diff):
        """Test that main uses --conn and --conn2 when both are provided."""
        mock_table_diff.return_value = MagicMock()

        with patch(
            "sys.argv",
            [
                "tablediff",
                "compare",
                "table_a",
                "table_b",
                "--pk",
                "id",
                "--conn",
                "duckdb://./db_a.duckdb",
                "--conn2",
                "duckdb://./db_b.duckdb",
            ],
        ):
            main()

        # Verify table_diff was called with different connections
        mock_table_diff.assert_called_once_with(
            "duckdb://./db_a.duckdb",  # conn_a
            "duckdb://./db_b.duckdb",  # conn_b
            "table_a",
            "table_b",
            "id",
            where=None,
        )

    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    @patch("tablediff.cli.render_id_samples")
    @patch("tablediff.cli.schema_diff")
    @patch("tablediff.cli.render_schema_diff")
    def test_main_extended_flag_works_with_cross_db(
        self, mock_schema_render, mock_schema_diff, mock_id_samples, mock_summary, mock_table_diff
    ):
        """Test that --extended flag works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()
        mock_schema_diff.return_value = MagicMock()

        with patch(
            "sys.argv",
            [
                "tablediff",
                "compare",
                "table_a",
                "table_b",
                "--pk",
                "id",
                "--conn",
                "duckdb://./db_a.duckdb",
                "--conn2",
                "duckdb://./db_b.duckdb",
                "--extended",
            ],
        ):
            main()

        # Verify extended output is rendered
        mock_summary.assert_called_once()
        mock_id_samples.assert_called_once()
        # Verify schema comparison is also rendered in extended mode
        mock_schema_diff.assert_called_once()
        mock_schema_render.assert_called_once()

    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_where_clause_works_with_cross_db(self, mock_render, mock_table_diff):
        """Test that --where clause works with cross-database comparison."""
        mock_table_diff.return_value = MagicMock()

        with patch(
            "sys.argv",
            [
                "tablediff",
                "compare",
                "table_a",
                "table_b",
                "--pk",
                "id",
                "--conn",
                "duckdb://./db_a.duckdb",
                "--conn2",
                "duckdb://./db_b.duckdb",
                "--where",
                'status = "active"',
            ],
        ):
            main()

        # Verify where clause is passed through
        mock_table_diff.assert_called_once_with(
            "duckdb://./db_a.duckdb", "duckdb://./db_b.duckdb", "table_a", "table_b", "id", where='status = "active"'
        )

    @patch("tablediff.cli.schema_diff")
    @patch("tablediff.cli.render_schema_diff")
    def test_main_schema_command(self, mock_render, mock_schema_diff):
        """Test that schema command calls schema_diff instead of table_diff."""
        mock_schema_diff.return_value = MagicMock()

        with patch("sys.argv", ["tablediff", "schema", "table_a", "table_b", "--conn", "duckdb://./db.duckdb"]):
            main()

        # Verify schema_diff was called
        mock_schema_diff.assert_called_once_with("duckdb://./db.duckdb", "duckdb://./db.duckdb", "table_a", "table_b")
        mock_render.assert_called_once()

    @patch("tablediff.cli.schema_diff")
    @patch("tablediff.cli.render_schema_diff")
    def test_main_schema_with_cross_db(self, mock_render, mock_schema_diff):
        """Test that schema command works with cross-database comparison."""
        mock_schema_diff.return_value = MagicMock()

        with patch(
            "sys.argv",
            [
                "tablediff",
                "schema",
                "table_a",
                "table_b",
                "--conn",
                "duckdb://./db_a.duckdb",
                "--conn2",
                "duckdb://./db_b.duckdb",
            ],
        ):
            main()

        # Verify schema_diff was called with different connections
        mock_schema_diff.assert_called_once_with(
            "duckdb://./db_a.duckdb", "duckdb://./db_b.duckdb", "table_a", "table_b"
        )
        mock_render.assert_called_once()

    @patch("tablediff.cli.load_csv_to_duckdb")
    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_csv_mode_uses_file_names(self, mock_render, mock_table_diff, mock_load_csv):
        """Test that CSV mode uses file names (without extensions) as table names."""
        mock_table_diff.return_value = MagicMock()
        mock_load_csv.return_value = ("duckdb:///tmp/csv.duckdb", "/tmp/csv.duckdb")

        with patch("tablediff.cli.os.path.exists", return_value=True):
            with patch(
                "sys.argv",
                [
                    "tablediff",
                    "files",
                    "/tmp/customers.csv",
                    "/tmp/orders.csv",
                    "--pk",
                    "id",
                ],
            ):
                main()

        mock_load_csv.assert_called_once_with(
            "/tmp/customers.csv", "/tmp/orders.csv", table_name_a="customers_csv", table_name_b="orders_csv"
        )
        mock_table_diff.assert_called_once_with(
            "duckdb:///tmp/csv.duckdb", "duckdb:///tmp/csv.duckdb", "customers_csv", "orders_csv", "id", where=None
        )

    @patch("tablediff.cli.load_csv_to_duckdb")
    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_csv_mode_same_file_names_add_suffixes(self, mock_render, mock_table_diff, mock_load_csv):
        """Test that CSV mode adds suffixes when file names match."""
        mock_table_diff.return_value = MagicMock()
        mock_load_csv.return_value = ("duckdb:///tmp/csv.duckdb", "/tmp/csv.duckdb")

        with patch("tablediff.cli.os.path.exists", return_value=True):
            with patch(
                "sys.argv",
                [
                    "tablediff",
                    "files",
                    "/tmp/data.csv",
                    "/var/data.csv",
                    "--pk",
                    "id",
                ],
            ):
                main()

        mock_load_csv.assert_called_once_with(
            "/tmp/data.csv", "/var/data.csv", table_name_a="data_csv_1", table_name_b="data_csv_2"
        )
        mock_table_diff.assert_called_once_with(
            "duckdb:///tmp/csv.duckdb", "duckdb:///tmp/csv.duckdb", "data_csv_1", "data_csv_2", "id", where=None
        )

    @patch("tablediff.cli.load_csv_to_duckdb")
    @patch("tablediff.cli.table_diff")
    @patch("tablediff.cli.render_summary_table")
    def test_main_csv_mode_sanitizes_spaces_and_dashes(self, mock_render, mock_table_diff, mock_load_csv):
        """Test that CSV mode replaces spaces and dashes with underscores."""
        mock_table_diff.return_value = MagicMock()
        mock_load_csv.return_value = ("duckdb:///tmp/csv.duckdb", "/tmp/csv.duckdb")

        with patch("tablediff.cli.os.path.exists", return_value=True):
            with patch(
                "sys.argv",
                [
                    "tablediff",
                    "files",
                    "/tmp/sales report-2024.csv",
                    "/tmp/shipments-2024.csv",
                    "--pk",
                    "id",
                ],
            ):
                main()

        mock_load_csv.assert_called_once_with(
            "/tmp/sales report-2024.csv",
            "/tmp/shipments-2024.csv",
            table_name_a="sales_report_2024_csv",
            table_name_b="shipments_2024_csv",
        )
        mock_table_diff.assert_called_once_with(
            "duckdb:///tmp/csv.duckdb",
            "duckdb:///tmp/csv.duckdb",
            "sales_report_2024_csv",
            "shipments_2024_csv",
            "id",
            where=None,
        )
