import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./talenthub_test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-thirty-two-characters")
os.environ.setdefault("TRUSTED_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.users.user import User, UserRole


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as session:
        session.add(
            User(
                email="student@talenthub.by",
                full_name="Анна Коваль",
                password_hash=hash_password("student-password"),
                role=UserRole.STUDENT,
            )
        )
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, base_url="http://localhost")
