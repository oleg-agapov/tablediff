# Test Suite Documentation

This directory contains comprehensive pytest unit tests for the tablediff package.

## Test Files

### test_engine.py
Tests for core functions in `tablediff/engine.py`:

1. **TestGetSchema**: Tests for `get_schema(db_path, table_name)`
   - Verifies schema retrieval from DuckDB databases
   - Tests qualified table names (schema.table)
   - Validates column metadata extraction

2. **TestQueryTable**: Tests for `query_table(db_path, table_name, columns, where)`
   - Verifies querying with specific columns
   - Tests WHERE clause filtering
   - Validates result set structure

3. **TestCalculateDifferences**: Tests for `calculate_differences(diffing_result)`
   - Tests diff calculation with added/removed/updated rows
   - Validates diff_by_keys and diff_by_sign structures
   - Tests composite primary key support

4. **TestTableDiff**: Tests for `table_diff(db_path, table_a_name, table_b_name, primary_key)`
   - End-to-end testing with real DuckDB databases
   - Validates DiffResult structure and statistics
   - Tests common column identification
   - Verifies diff categorization (added/removed/updated)

### test_reladiff_integration.py
Tests for integration with the external `reladiff` package using mocking:

1. **TestConnectToTableIntegration**: Tests for `connect_to_table` function interactions
   - Validates correct parameters passed to reladiff
   - Tests qualified table name handling
   - Verifies TableSegment objects are created correctly

2. **TestDiffTablesIntegration**: Tests for `diff_tables` function interactions
   - Validates key_columns and extra_columns parameters
   - Tests WHERE clause propagation
   - Verifies statistics parsing from diff_tables results
   - Tests result_list processing

3. **TestReladiffErrorHandling**: Tests for error handling
   - Connection error propagation
   - Invalid key error handling

## Test Data

Tests use temporary DuckDB databases created with pytest's `tmp_path` fixture. The test database includes:

- **users_a table**: 4 rows with columns (id, name, email, age)
- **users_b table**: 4 rows with known differences:
  - Row 1: unchanged
  - Row 2: updated (different email)
  - Row 3: removed (not in table B)
  - Row 4: updated (different email and age)
  - Row 5: added (not in table A)

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_engine.py -v
```

### Run specific test class
```bash
pytest tests/test_engine.py::TestGetSchema -v
```

### Run specific test
```bash
pytest tests/test_engine.py::TestGetSchema::test_get_schema_returns_columns -v
```

### Run with coverage
```bash
pytest tests/ --cov=tablediff --cov-report=html
```

## Requirements

The test suite requires the following packages:
- pytest
- pytest-mock
- duckdb
- reladiff

Install with:
```bash
pip install -e ".[dev,duckdb]"
```

## Test Design Principles

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Fixtures**: Uses pytest fixtures for setup/teardown of test databases
3. **Mocking**: External dependencies (reladiff) are mocked to avoid network access
4. **Descriptive Names**: Test names clearly describe what is being tested
5. **Documentation**: Comments explain what each test verifies
6. **Real Data**: Integration tests use actual DuckDB databases where possible
7. **No Network**: All tests run locally without requiring network access

## Test Coverage

The test suite covers:
- ✅ Schema retrieval (`get_schema`)
- ✅ Table querying (`query_table`)
- ✅ Difference calculation (`calculate_differences`)
- ✅ End-to-end table diffing (`table_diff`)
- ✅ Integration with reladiff (`connect_to_table`, `diff_tables`)
- ✅ Error handling for external dependencies

Total: 25 tests covering all core functionality
