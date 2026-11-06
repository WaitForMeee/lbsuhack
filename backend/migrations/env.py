from logging.config import fileConfig

import app.models  # noqa: F401
from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.db.engine import (
    create_database_engine,
    prepare_migration_schema,
    quoted_schema,
)
from sqlalchemy import pool

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    from sqlalchemy.engine import make_url

    is_postgresql = make_url(settings.database_url).get_backend_name() == "postgresql"
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        version_table_schema=settings.database_schema if is_postgresql else None,
    )
    with context.begin_transaction():
        if is_postgresql:
            schema = quoted_schema(settings.database_schema)
            context.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            context.execute(f"SET SESSION search_path TO {schema}")
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_database_engine(
        settings.database_url,
        settings.database_schema,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        prepare_migration_schema(connection, settings.database_schema)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            version_table_schema=settings.database_schema
            if connection.dialect.name == "postgresql"
            else None,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
