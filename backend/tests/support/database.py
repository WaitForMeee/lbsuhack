from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def migrated_database():
    from alembic import command
    from alembic.config import Config
    from app.core.config import get_settings
    from app.db.session import engine

    # The same DATABASE_SCHEMA selects both app and migration connections.
    schema = get_settings().database_schema
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
            from app.scripts.seed_demo import DEMO_ORGANIZATION_TOKENS
            is_org = persona in DEMO_ORGANIZATION_TOKENS
            response = client.post(
                "/api/v1/auth/organization-login" if is_org else "/api/v1/auth/login",
                json={"token": DEMO_ORGANIZATION_TOKENS[persona]} if is_org else {"email": persona + "@demo.by", "password": "demo1234"},
            )
            assert response.status_code == 200, response.text
            cache[persona] = {
                "Authorization": "Bearer " + response.json()["access_token"]
            }
        return cache[persona]

    return headers
