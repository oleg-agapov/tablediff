from __future__ import annotations

from pathlib import Path
import os
import re
from typing import Any, Iterable

import snowflake.connector
import yaml


def _quote_ident(name: str) -> str:
	cleaned = name.strip().strip('"')
	escaped = cleaned.replace('"', '""')
	return f'"{escaped}"'


_ENV_VAR_PATTERN = re.compile(r"\{\{\s*env_var\(['\"]([^'\"]+)['\"]\)\s*\}\}")


def _resolve_env_template(value: Any) -> Any:
	if isinstance(value, str):
		match = _ENV_VAR_PATTERN.fullmatch(value.strip())
		if match:
			env_key = match.group(1)
			try:
				return os.environ[env_key]
			except KeyError as exc:  # pragma: no cover - clearer error message
				raise RuntimeError(f"Environment variable '{env_key}' is not set.") from exc
	return value


def _load_profile(profile_path: Path) -> dict[str, Any]:
	if not profile_path.exists():
		raise FileNotFoundError(f"Profile file '{profile_path}' not found.")

	with profile_path.open("r", encoding="utf-8") as fh:
		data = yaml.safe_load(fh) or {}

	if not isinstance(data, dict):
		raise ValueError("profiles.yml must contain a mapping at the top level.")
	return data


class SnowflakeAdapter:
	def __init__(
		self,
		*,
		account: str,
		user: str,
		password: str,
		warehouse: str,
		database: str,
		schema: str,
		role: str | None = None,
		authenticator: str | None = None,
		connection: Any | None = None,
	) -> None:
		self._database = database
		self._schema = schema

		if connection is not None:
			self._conn = connection
		else:
			conn_kwargs: dict[str, Any] = {
				"account": account,
				"user": user,
				"password": password,
				"warehouse": warehouse,
				"database": database,
				"schema": schema,
			}
			if role:
				conn_kwargs["role"] = role
			if authenticator:
				conn_kwargs["authenticator"] = authenticator

			self._conn = snowflake.connector.connect(**conn_kwargs)

	def run_sql(self, statement: str) -> list[tuple[Any, ...]]:
		cursor = self._conn.cursor()
		try:
			cursor.execute(statement)
			return cursor.fetchall()
		finally:
			cursor.close()

	def run_statements(self, statements: Iterable[str]) -> None:
		for statement in statements:
			self.run_sql(statement)

	def _quote_table(self, table: str) -> str:
		parts = [part for part in (segment.strip() for segment in table.split(".")) if part]
		if not parts:
			raise ValueError("Table name must not be empty.")
		return ".".join(_quote_ident(part) for part in parts)

	def get_columns(self, table: str) -> list[str]:
		table_ref = self._quote_table(table)
		rows = self.run_sql(f"DESCRIBE TABLE {table_ref}")
		return [str(row[0]) for row in rows if row and row[0]]

	def count_rows(self, table: str) -> int:
		table_ref = self._quote_table(table)
		query = f"SELECT COUNT(*) FROM {table_ref}"
		return int(self.run_sql(query)[0][0])

	def count_duplicate_pks(self, table: str, pk: str) -> int:
		table_ref = self._quote_table(table)
		pk_q = _quote_ident(pk)
		query = f"""
			SELECT COUNT(*) FROM (
				SELECT {pk_q} AS pk
				FROM {table_ref}
				GROUP BY {pk_q}
				HAVING COUNT(*) > 1
			) dup
		"""
		return int(self.run_sql(query)[0][0])

	def diff_counts(
		self,
		table_a: str,
		table_b: str,
		pk: str,
		common_columns: Iterable[str],
	) -> dict[str, int]:
		col_checks = []
		for col in common_columns:
			col_q = _quote_ident(col)
			col_checks.append(f"a.{col_q} IS NOT DISTINCT FROM b.{col_q}")

		all_equal = " AND ".join(col_checks) if col_checks else "TRUE"

		pk_q = _quote_ident(pk)
		table_a_ref = self._quote_table(table_a)
		table_b_ref = self._quote_table(table_b)

		query = f"""
			SELECT
				SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NULL THEN 1 ELSE 0 END) AS only_in_a,
				SUM(CASE WHEN a.{pk_q} IS NULL AND b.{pk_q} IS NOT NULL THEN 1 ELSE 0 END) AS only_in_b,
				SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NOT NULL AND ({all_equal}) THEN 1 ELSE 0 END) AS in_both_same,
				SUM(CASE WHEN a.{pk_q} IS NOT NULL AND b.{pk_q} IS NOT NULL AND NOT ({all_equal}) THEN 1 ELSE 0 END) AS in_both_diff
			FROM {table_a_ref} AS a
			FULL OUTER JOIN {table_b_ref} AS b
			ON a.{pk_q} = b.{pk_q}
		"""
		row = self.run_sql(query)[0]
		return {
			"only_in_a": int(row[0]),
			"only_in_b": int(row[1]),
			"in_both_same": int(row[2]),
			"in_both_diff": int(row[3]),
		}

	@classmethod
	def from_profile(
		cls,
		profile_path: str | Path,
		profile_name: str,
		target_name: str,
	) -> SnowflakeAdapter:
		path = Path(profile_path)
		profile_data = _load_profile(path)

		try:
			profile_entry = profile_data[profile_name]
			target_entry = profile_entry["outputs"][target_name]
		except KeyError as exc:  # pragma: no cover - defensive guard
			raise ValueError(
				f"Profile '{profile_name}' with target '{target_name}' not found in {path}."
			) from exc

		resolved = {key: _resolve_env_template(target_entry.get(key)) for key in target_entry}

		required_keys = ["account", "user", "password", "warehouse", "database", "schema"]
		missing = [key for key in required_keys if not resolved.get(key)]
		if missing:
			missing_keys = ", ".join(missing)
			raise ValueError(f"Missing required Snowflake settings: {missing_keys}.")

		return cls(
			account=str(resolved["account"]),
			user=str(resolved["user"]),
			password=str(resolved["password"]),
			warehouse=str(resolved["warehouse"]),
			database=str(resolved["database"]),
			schema=str(resolved["schema"]),
			role=str(resolved.get("role")) if resolved.get("role") else None,
			authenticator=str(resolved.get("authenticator")) if resolved.get("authenticator") else None,
		)

