"""
Pytest configuration and shared fixtures for tablediff tests.
"""

import pytest
import duckdb


@pytest.fixture
def simple_duckdb(tmp_path):
    """
    Create a simple temporary DuckDB database with a single table.
    
    Useful for basic schema and query tests.
    """
    db_path = tmp_path / "simple.duckdb"
    conn = duckdb.connect(str(db_path))
    
    conn.execute("""
        CREATE TABLE simple_table (
            id INTEGER PRIMARY KEY,
            value VARCHAR
        )
    """)
    
    conn.execute("""
        INSERT INTO simple_table VALUES
        (1, 'one'),
        (2, 'two'),
        (3, 'three')
    """)
    
    conn.close()
    
    yield str(db_path)


# Configure pytest to show full assertion diffs
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
