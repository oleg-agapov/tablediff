# tablediff
CLI tool for data diffing between two tables

## Local development

```bash
# Setup virtual environment
uv venv .venv
source .venv/bin/activate

# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Create sample database
tablediff generate-example

# Run table diffing
tablediff table_a table_b --pk id --db data/example.duckdb
```

## Generating sample DuckDB for local testing

To generate local DuckDB database with the same cases as in /tests run:

```bash
python generate-sample.py --db-path sample.duckdb
```
