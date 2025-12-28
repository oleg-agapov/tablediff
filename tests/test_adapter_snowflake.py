from __future__ import annotations

from pathlib import Path

import pytest

from tablediff.adapters.snowflake import SnowflakeAdapter


class _FakeConnection:
    def cursor(self):  # pragma: no cover - not used directly in these tests
        raise AssertionError("cursor should not be used in this test")


def test_from_profile_resolves_env_placeholders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile_path = tmp_path / "profiles.yml"
    profile_path.write_text(
        """
profile_1:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: hiive-prod
      database: DEV
      warehouse: DEV_WAREHOUSE
      role: DEV_ROLE
      authenticator: username_password_mfa
      schema: "{{ env_var('DBT_SCHEMA') }}"
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
        """
    )

    monkeypatch.setenv("DBT_SCHEMA", "DBT_OLEG")
    monkeypatch.setenv("DBT_USER", "oleg@example.com")
    monkeypatch.setenv("DBT_PASSWORD", "super-secret")

    captured: dict[str, str] = {}

    def fake_connect(**kwargs):
        captured.update({key: str(value) for key, value in kwargs.items()})
        return _FakeConnection()

    monkeypatch.setattr(
        "tablediff.adapters.snowflake.snowflake.connector.connect",
        fake_connect,
    )

    SnowflakeAdapter.from_profile(profile_path, "profile_1", "dev")

    assert captured["schema"] == "DBT_OLEG"
    assert captured["user"] == "oleg@example.com"
    assert captured["password"] == "super-secret"
    assert captured["role"] == "DEV_ROLE"
    assert captured["authenticator"] == "username_password_mfa"


def test_quote_table_handles_multi_part_names() -> None:
    adapter = SnowflakeAdapter(
        account="acc",
        user="user",
        password="pwd",
        warehouse="wh",
        database="db",
        schema="schema",
        connection=_FakeConnection(),
    )

    quoted = adapter._quote_table("DEV.PUBLIC.items")

    assert quoted == '"DEV"."PUBLIC"."items"'
