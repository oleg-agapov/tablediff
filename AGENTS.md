# AGENTS.md

Agent instructions for the `tablediff` repository.

## Scope
These instructions apply to the entire repository rooted at this file.

## Repository purpose
`tablediff` is a Python CLI for comparing:
- two database tables (`tablediff compare`),
- table schemas (`tablediff schema`),
- two CSV files loaded into temporary DuckDB (`tablediff files`).

Core package lives in `tablediff/`; tests live in `tests/`.

## Tech stack
- Python >= 3.10
- Packaging/build: `setuptools` + `pyproject.toml`
- Env/tooling: `uv`
- Linting: `ruff`
- Typing: `mypy`
- Tests: `pytest`
- CLI rendering: `rich`
- Diff engine: `reladiff`

## Fast-start commands
```bash
# install runtime + dev deps
uv sync --extra dev

# run tests
uv run pytest

# lint + format checks
uv run ruff check .
uv run ruff format --check .

# type checks
uv run mypy tablediff

# run CLI
uv run tablediff --help
```

## File map (high signal)
- `tablediff/cli.py` — argparse command structure and command routing.
- `tablediff/engine.py` — core comparison logic + CSV-to-DuckDB loading.
- `tablediff/renderers.py` — console output formatting.
- `tablediff/models.py` — dataclasses/models returned by engine.
- `tests/test_cli.py` — CLI behavior coverage.
- `tests/test_engine.py`, `tests/test_csv.py`, `tests/test_cross_database.py` — core engine behaviors.
- `tests/test_reladiff_integration.py` — reladiff integration expectations.

## Agent workflow expectations
1. **Read before editing**
   - Inspect the relevant module and associated tests first.
   - Preserve public CLI semantics unless task explicitly requires changing them.

2. **Prefer minimal, targeted diffs**
   - Avoid broad refactors unless requested.
   - Keep function signatures stable when possible.

3. **Update tests with behavior changes**
   - Any functional change should include or adjust tests in `tests/`.
   - Prefer focused unit tests over broad integration additions.

4. **Run quality gates before finishing**
   - At minimum run tests touched by your change.
   - For non-trivial changes, run full `uv run pytest`, `uv run ruff check .`, and `uv run mypy tablediff`.

5. **Document user-visible changes**
   - Update `README.md` when CLI flags/behavior/examples change.
   - Add a concise `CHANGELOG.md` entry for notable user-facing changes.

## Coding conventions
- Follow existing style and naming patterns in nearby files.
- Keep imports clean and ordered (ruff/isort-compatible).
- Prefer explicit type hints on new/modified public functions.
- Keep line length within Ruff config (120).
- Avoid adding new dependencies unless clearly justified.

## CLI and diffing guardrails
- Treat `--conn` as primary connection for table A and default for table B unless `--conn2` is supplied.
- Preserve support for cross-database comparisons.
- For CSV comparison:
  - maintain safe table-name sanitization,
  - avoid SQL injection risks,
  - ensure temporary DuckDB file cleanup remains reliable.

## Testing guidance
Use these selective commands when iterating:
```bash
uv run pytest tests/test_cli.py -q
uv run pytest tests/test_engine.py tests/test_csv.py -q
uv run pytest tests/test_cross_database.py -q
```
Run the full suite before completing significant changes.

## Commit guidance
- Use clear, imperative commit messages.
- Keep each commit focused on one logical change.
- In PR descriptions, include: what changed, why, how tested, and any follow-ups.
