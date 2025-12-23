# Python CLI Tool for Data Diffing Between Two Tables

## 1. Overview

Build a Python-based CLI tool that compares ("diffs") two database tables and helps users understand how data differs between them. The tool should work across different database types via adapters, output results in multiple formats (summary / JSON / Markdown), and provide an interactive terminal UI using the Rich library.

## 2. Goals

- Compare two tables at row level, using a primary key (PK) as the row identity.
- Validate that the PK is unique in each table before diffing.
- Compare only common columns (intersection of column names) shared by both tables.
- Produce a clear summary of matches/differences.

## 3. Non-goals (initial scope boundaries)

- Not attempting full schema migration or automated reconciliation.
- Not comparing non-overlapping columns (only intersection).
- Not building a web UI (terminal-only).
- Not supporting fuzzy matching or approximate joins (strict PK match).

## 4. User Experience

### CLI Entry Point

User provides two table references and a primary key.

Example (conceptual):

```
diff table_a table_b --pk id
```

(optional later) connection strings / profiles / config files

### High-Level Flow

1. Load schemas for both tables.
2. Identify common columns (intersection).
3. Validate PK exists in both and is unique in both.
4. Compute diff results:
    - rows only in A
    - rows only in B
    - rows in both and identical (across common columns)
    - rows in both but different (across common columns)
5. Display results in selected output format.
6. If in interactive mode, open a Rich-driven exploration UI.

## 5. Core Features

A. Schema & Column Handling

- Determine column lists for each table.
- Compute `common_columns = columns_a ∩ columns_b`.
- Ensure primary key column exists in both.

B. Primary Key Validation

- Verify PK uniqueness in each table.
- If duplicates exist:
    - fail fast with a clear error
    - show count of duplicates (and ideally sample duplicate keys)

C. Diff Computation (Row-Level)

Using primary key as the join key, produce:
- `only_in_a`: PKs present in A but not B
- `only_in_b`: PKs present in B but not A
- `in_both_same`: PKs present in both and all common columns equal
- `in_both_different`: PKs present in both but at least one common column differs
    - Track which columns differ per PK (for drill-down)

D. Summary Output

At minimum:

- Total rows in A / B
- Common columns count/list (optional list)
- PK uniqueness status in each table
- Counts:
    - same
    - different
    - only in A
    - only in B

E. Interactive Exploration (Rich UI)

After diff completes, the program waits for user input via a terminal UI.
Interactive options should include:

- Preview records only in A
    - show first 5 rows from A whose PK not in B
- Preview records only in B
    - show first 5 rows from B whose PK not in A
- Inspect a mismatched record
    - select a PK from in_both_different
    - show row from A and row from B side-by-side (or stacked)
    - highlight columns that differ
(Optional but useful) filter/search by PK

## 6. Architecture & Components

1. Core Diff Logic (Engine)

Responsibilities:
- schema inspection (via adapter)
- PK validation
- diff calculation
- produce a structured result object that UI/renderers can consume

Suggested internal data model (conceptual):
- DiffResult
- table_a_meta, table_b_meta
- primary_key
- common_columns
- counts (same, different, only_a, only_b)
- only_in_a_pks, only_in_b_pks
- different_pks
- diff_columns_by_pk (pk -> list of differing columns)

2. Presentation Layer (Renderers / Output Formats)

Responsibilities:
- convert DiffResult into:
    - human-readable summary (default)
    - JSON output (machine-readable)
    - Markdown output (paste into GitHub/Notion)

3. Adapters (Database Connectivity)

Responsibilities:
- connect to a data source
- fetch table schema (column names/types if available)
- read PK list
- fetch rows by PK (for preview/inspection)
- run queries efficiently for:
- PK uniqueness check
- diff computation / sampling

Adapters should allow supporting multiple backends later (e.g., Postgres, Snowflake, BigQuery, DuckDB, SQLite) without changing the core diff logic.

## 7. Functional Requirements

Minimal Working Product (MWP)

Core Value Proposition

| Given two tables and a primary key, tell me how similar they are and where they differ, safely.

If this works reliably, everything else (Rich UI, previews, formats) is incremental.

What the MWP must do

1. CLI Interface (minimal)

Single command, minimal flags:
```
datadiff table_a table_b --pk id
```
No interactive mode. No fancy UI.

2. Schema & Column Handling

Load column names for both tables
Compute:
```
common_columns = intersection(table_a.columns, table_b.columns)
```
If no common columns → fail with a clear error
This is essential because it defines the comparison scope.

3. Primary Key Validation (critical)

For each table:
- Ensure PK column exists
- Ensure PK values are unique

If PK is not unique:
- Exit with non-zero code

Print:
- which table failed
- number of duplicate PKs

This is non-negotiable, even for MVP.

4. Row Classification (core diff logic)

Using the PK, calculate categories:

- only_in_a -- PK exists in A, not in B
- only_in_b -- PK exists in B, not in A
- in_both_same -- PK exists in both and all common columns equal
- in_both_different -- PK exists in both and ≥1 common column differs

⚠️ For MWP:
You do not need to store per-column diffs
Just classify rows

5. Summary Output (stdout only)

Human-readable text, no formatting options:
Example:

```
Data diff summary
-----------------
Primary key: id

Table A rows: 120_000
Table B rows: 118_450
Common columns: 12

Rows only in A:        3,200
Rows only in B:        1,650
Rows in both (same):   112,900
Rows in both (diff):   4,250
```

That's it.
No JSON, no Markdown, no previews.

What the MWP explicitly does NOT include

❌ Interactive mode
❌ Rich UI
❌ Row previews
❌ Column-level diff reporting
❌ Multiple output formats
❌ Config files / profiles
❌ Performance optimizations beyond correctness

This keeps scope tight and implementation fast.



## 8. Success Criteria

User can run one command to compare two tables and immediately see:
- whether PK is safe to diff on
- how much matches vs differs
Core engine remains adapter-agnostic and output-format agnostic.

## 9. Risks & Considerations

- Scale: diffing very large tables may require query pushdown / hashing strategies.
- NULL semantics: define equality rules (e.g., NULL = NULL treated as equal).
- Type mismatches: same column name but different types—decide whether to cast or warn.
- Ordering: previews should be stable and predictable.

## 10. Deliverables

Python package with:
- CLI entry point
- diff engine module
- adapters module
- renderers module

Documentation:
- install + quickstart
- examples
- adapter implementation guide

Basic test suite:
- PK uniqueness validation tests
- diff classification tests
- renderer output tests
