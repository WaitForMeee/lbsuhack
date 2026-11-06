import re

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine, make_url


def quoted_schema(schema: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise ValueError("Invalid PostgreSQL schema name")
    return f'"{schema}"'


def create_database_engine(url: str, schema: str, **options) -> Engine:
    options.setdefault("pool_pre_ping", True)
    if make_url(url).get_backend_name() == "sqlite":
        options.setdefault("connect_args", {"check_same_thread": False})
    engine = create_engine(url, **options)
    if engine.dialect.name == "postgresql":
        search_path = f"SET SESSION search_path TO {quoted_schema(schema)}"

        @event.listens_for(engine, "connect", insert=True)
        def set_search_path(connection, record):
            # Keep the session setting when SQLAlchemy rolls back a transaction.
            previous_autocommit = connection.autocommit
            connection.autocommit = True
            try:
                with connection.cursor() as cursor:
                    cursor.execute(search_path)
            finally:
                connection.autocommit = previous_autocommit

    elif engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


def prepare_migration_schema(connection: Connection, schema: str) -> None:
    if connection.dialect.name != "postgresql":
        return
    quoted = quoted_schema(schema)
    connection.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {quoted}")
    connection.exec_driver_sql(f"SET SESSION search_path TO {quoted}")
    connection.commit()
    # Reflection must treat this as the default schema, including on first creation.
    connection.dialect.default_schema_name = schema
