# tablediff
CLI tool for data diffing between two tables

## Local development

```bash
# Setup virtual environment
uv sync --extra dev
source .venv/bin/activate

# Run tests
pytest

# Run table diffing (DuckDB)
tablediff table_a table_b --pk id --conn duckdb://./sample.duckdb
```

## Generating sample DuckDB for local testing

To generate local DuckDB database with the same cases as in /tests run:

```bash
python generate-sample.py --db-path sample.duckdb
```

Alternatively, use Python scripts:

```
python scripts/generate_duckdb_test_data.py \
  --db-path sample.duckdb \
  --prod-rows 23753 \
  --dev-remove-rows 342 \
  --dev-add-rows 30 \
  --dev-null-status-rows 578
```

And then:

```
tablediff users_dev users_prod --pk id --conn duckdb://./sample.duckdb
```
