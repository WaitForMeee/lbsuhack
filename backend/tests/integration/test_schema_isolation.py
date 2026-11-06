"""PostgreSQL-only regression for a legacy Alembic revision in another schema."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.db.engine import create_database_engine
from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.engine import make_url

pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="PostgreSQL schema isolation requires TALENTHUB_TEST_DATABASE_URL",
)
ROOT = Path(__file__).resolve().parents[2]


def test_legacy_revision_and_rows_survive_new_schema_migration_and_seed():
    old_schema = "test_old_" + uuid4().hex
    new_schema = "test_new_" + uuid4().hex
    base_url = get_settings().database_url
    # Simulate a connection URL/role that points to the legacy schema by default.
    url = (
        make_url(base_url)
        .update_query_dict({"options": "-csearch_path=" + old_schema})
        .render_as_string(hide_password=False)
    )
    old_engine = create_database_engine(base_url, old_schema)
    new_engine = create_database_engine(url, new_schema)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{old_schema}"')
        with old_engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"
            )
            connection.exec_driver_sql(
                "INSERT INTO alembic_version VALUES ('20261105_0002')"
            )
            connection.exec_driver_sql(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
            )
            connection.exec_driver_sql("INSERT INTO users VALUES (1, 'Legacy student')")
        environment = {**os.environ, "DATABASE_URL": url, "DATABASE_SCHEMA": new_schema}
        for command in (
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            [sys.executable, "-m", "app.scripts.seed_demo"],
            [sys.executable, "-m", "alembic", "upgrade", "head"],
        ):
            result = subprocess.run(
                command, cwd=ROOT, env=environment, capture_output=True, text=True
            )
            assert result.returncode == 0, result.stderr
        with new_engine.connect() as connection:
            assert connection.scalar(text("SELECT current_schema()")) == new_schema
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "20261106_0002"
            )
            assert connection.scalar(text("SELECT count(*) FROM users")) == 11
        with old_engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "20261105_0002"
            )
            assert connection.execute(text("SELECT id,name FROM users")).all() == [
                (1, "Legacy student")
            ]
    finally:
        old_engine.dispose()
        new_engine.dispose()
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{new_schema}" CASCADE')
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{old_schema}" CASCADE')
