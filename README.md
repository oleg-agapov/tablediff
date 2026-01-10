# tablediff

CLI tool for data diffing between two tables:

![Screenshot of the tool](https://raw.githubusercontent.com/oleg-agapov/tablediff/refs/heads/main/img/screenshot.png)

## Installation

The package is available in PyPi and can be installed by specifying the package name and the adapter for your database.

Currently it was tested with DuckDB and Snowflake, but technically should support all adapters that [reladiff supports](https://reladiff.readthedocs.io/en/latest/supported-databases.html):

| Adapter   | Command                                      |
|-----------|----------------------------------------------|
| DuckDB    | ``` pip install tablediff-cli[duckdb] ```    |
| Snowflake | ``` pip install tablediff-cli[snowflake] ``` |

To install all available adapters try:

```
pip install tablediff-cli[all]
```

Requires Python 3.10+. Technically can be downported to earlier versions, let me know if you need it.

## Usage

Once installed, use command-line to run the diffing process:

```
tablediff TABLE_A TABLE_B --pk PRIMARY_KEY --conn CONNECTION_STRING [OPTIONS]
```

- tables should be in format `table_name` or `schema.table_name` or `database.schema.table_name`
  - for Snowflake use all identifiers in UPPERCASE
- `--pk` is the primary key column (should exist in both tables)
- `--conn` is the database connection string

Here are a could of examples of connection strings:

- DuckDB
  ``` 
  duckdb://<file_path>
  ```

- Snowflake
  ```
  "snowflake://<user>[:<password>]@<account>/<database>/<SCHEMA>?warehouse=<WAREHOUSE>&role=<role>[&authenticator=externalbrowser]" 
  ```

For other databases check [docs for reladiff](https://reladiff.readthedocs.io/en/latest/supported-databases.html).

## Examples

Diffing in DuckDB:

```
tablediff users_prod users_dev --pk id --conn duckdb://./sample.duckdb
```

Diffing in Snowflake:

```
tablediff DEV.MART.USERS PROD.MART.USERS \
  --pk USER_ID \
  --conn "snowflake://..."
```

## Additional flags

### --extended
If you pass `--extended` flag you'll get an extended output that will show you:

- Common and unique columns in both tables
- For rows, it will return:
  - 5 id's that are not matching
  - 5 id's that exist only in table A and B

### --where

Allows to pass additional WHERE condition that will be applied to both tables:

```
tablediff table_a table_b \
  --pk id \
  --conn snowflake://... \
  --where "created_at >= CURRENT_DATE - 7 and status = 'active'"
```

# Package development

Clone the repo:

```
git clone git@github.com:oleg-agapov/tablediff.git
```

Now setup the local environment (I'm using uv):

```bash
# Setup virtual environment
uv sync --extra dev
source .venv/bin/activate

# Run tests
pytest
```

## Generating sample DuckDB for local testing


Use Python script:

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

# Future roadmap

- [x] WHERE conditions
- [x] Add tests
- [ ] Schema-only comparison (with data types)
- [ ] Column-by-column comparison (# of rows that are different)
- [ ] Add pre-commit hooks (check vesion bump?)
- [ ] Add dbt support
