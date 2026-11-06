import os
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture(scope="session")
def migrated_database():
    from alembic import command
    from alembic.config import Config
    from app.db.session import engine

    # PostgreSQL runs get a unique schema; even a valid test DB keeps other schemas intact.
    schema = "test_" + uuid4().hex
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def search_path(connection, record):
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema}"')
            connection.commit()

        engine.dispose()
        os.environ["TALENTHUB_MIGRATION_TEST_SCHEMA"] = schema
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")
    yield
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
    engine.dispose()


@pytest.fixture
def reset_database(migrated_database):
    from app.db.base import Base
    from app.db.session import SessionLocal
    from app.scripts.seed_demo import seed_demo
    from sqlalchemy import delete

    # Delete data only in the schema/file created by this test process.
    with SessionLocal.begin() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        seed_demo(db)


@pytest.fixture
def client():
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="http://api.test") as client:
        yield client


@pytest.fixture
def auth(client):
    cache = {}

    def headers(persona):
        if persona not in cache:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": persona + "@demo.by", "password": "demo1234"},
            )
            assert response.status_code == 200, response.text
            cache[persona] = {
                "Authorization": "Bearer " + response.json()["access_token"]
            }
        return cache[persona]

    return headers
