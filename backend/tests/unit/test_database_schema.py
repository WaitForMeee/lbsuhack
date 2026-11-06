from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from app.core.config import Settings
from app.db import engine as database_engine
from pydantic import ValidationError


@pytest.mark.parametrize(
    "schema", ["", "public; DROP SCHEMA public CASCADE", 'a"b', "with space", "a" * 64]
)
def test_schema_name_validation(schema):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_schema=schema)
    with pytest.raises(ValueError):
        database_engine.quoted_schema(schema)


def test_new_connections_select_only_v2_schema_outside_transactions(monkeypatch):
    engine = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    listeners = {}
    monkeypatch.setattr(
        database_engine, "create_engine", lambda *args, **kwargs: engine
    )

    def listens_for(target, event, **options):
        assert target is engine and options["insert"] is True

        def register(callback):
            listeners[event] = callback
            return callback

        return register

    monkeypatch.setattr(database_engine.event, "listens_for", listens_for)
    database_engine.create_database_engine(
        "postgresql+psycopg://localhost/example", "talenthub_v2"
    )
    connection = MagicMock()
    connection.autocommit = False
    cursor = connection.cursor.return_value.__enter__.return_value

    def execute(statement):
        assert connection.autocommit is True
        assert statement == 'SET SESSION search_path TO "talenthub_v2"'

    cursor.execute.side_effect = execute
    listeners["connect"](connection, None)
    assert connection.autocommit is False
    # The setting was committed by autocommit, not left inside a rolled-back transaction.
    connection.commit.assert_not_called()


def test_schema_setup_creates_only_selected_schema_before_version_lookup():
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    database_engine.prepare_migration_schema(connection, "talenthub_v2")
    assert [call.args[0] for call in connection.exec_driver_sql.call_args_list] == [
        'CREATE SCHEMA IF NOT EXISTS "talenthub_v2"',
        'SET SESSION search_path TO "talenthub_v2"',
    ]
    connection.commit.assert_called_once_with()
    assert connection.dialect.default_schema_name == "talenthub_v2"


def test_sqlite_schema_setup_is_unchanged():
    connection = MagicMock()
    connection.dialect.name = "sqlite"
    database_engine.prepare_migration_schema(connection, "talenthub_v2")
    connection.exec_driver_sql.assert_not_called()
