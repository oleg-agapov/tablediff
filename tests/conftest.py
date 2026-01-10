"""
Pytest configuration and shared fixtures for tablediff tests.
"""

import pytest
import duckdb


@pytest.fixture
def temp_duckdb(tmp_path):
    """
    Create a temporary DuckDB database with sample tables for testing.
    
    Creates two tables:
    - table_a: with columns (id, name, email, age)
    - table_b: with columns (id, name, email, age)
    
    With sample data to test added, removed, and updated rows.
    """
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    
    # Create table A with initial data
    conn.execute("""
        CREATE TABLE table_a (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            age INTEGER
        )
    """)
    
    conn.execute("""
        INSERT INTO table_a VALUES
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
        CREATE TABLE table_b (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            age INTEGER
        )
    """)
    
    conn.execute("""
        INSERT INTO table_b VALUES
        (1, 'Alice', 'alice@example.com', 30),
        (2, 'Bob', 'bob_new@example.com', 25),
        (4, 'David', 'david_new@example.com', 29),
        (5, 'Eve', 'eve@example.com', 27)
    """)
    
    # Create table C and D with different columns for testing extra_columns
    conn.execute("""
        CREATE TABLE table_c (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            status VARCHAR
        )
    """)
    
    conn.execute("""
        INSERT INTO table_c VALUES
        (1, 'Alice', 'alice@example.com', 'active'),
        (2, 'Bob', 'bob@example.com', 'inactive')
    """)
    
    conn.execute("""
        CREATE TABLE table_d (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            role VARCHAR
        )
    """)
    
    conn.execute("""
        INSERT INTO table_d VALUES
        (1, 'Alice', 'alice@example.com', 'admin'),
        (2, 'Bob', 'bob@example.com', 'user')
    """)
    
    conn.close()
    
    yield str(db_path)
    
    # Cleanup is handled by tmp_path fixture


# Configure pytest to show full assertion diffs
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
