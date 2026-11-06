import os
from logging.config import fileConfig

import app.models  # noqa: F401
from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from sqlalchemy import engine_from_config, pool

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        test_schema = os.environ.get("TALENTHUB_MIGRATION_TEST_SCHEMA")
        if test_schema:
            import re

            if not re.fullmatch(r"test_[a-f0-9]{32}", test_schema):
                raise RuntimeError("Invalid isolated test schema")
            if not (connection.engine.url.database or "").startswith("talenthub_test"):
                raise RuntimeError("Test schema requires a talenthub_test database")
            connection.exec_driver_sql(f'SET search_path TO "{test_schema}"')
            connection.commit()
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
