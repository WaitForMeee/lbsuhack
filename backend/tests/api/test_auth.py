from datetime import timedelta

import pytest
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models import User
from sqlalchemy import select

API = "/api/v1"


@pytest.mark.parametrize(
    "persona,role",
    [
        ("alina", "student"),
        ("olga", "parent"),
        ("school", "school"),
        ("company", "company"),
        ("admin", "moderator"),
    ],
)
def test_five_logins(client, persona, role):
    from app.scripts.seed_demo import DEMO_ORGANIZATION_TOKENS
    response = client.post(
        API + ("/auth/organization-login" if role in ("school", "company") else "/auth/login"),
        json=dict(token=DEMO_ORGANIZATION_TOKENS[persona], expected_role=role) if role in ("school", "company") else dict(email=persona + "@demo.by", password="demo1234", expected_role=role),
    )
    assert response.status_code == 200
    session = response.json()
    assert session["expires_in"] == 28800 and session["token_type"] == "bearer"
    assert not response.cookies
    headers = {"Authorization": "Bearer " + session["access_token"]}
    assert client.get(API + "/auth/me", headers=headers).json()["role"] == role
    assert client.get(API + "/auth/me").status_code == 401


def test_auth_failures(client, auth):
    for body in [
        dict(email="alina@demo.by", password="wrong"),
        dict(email="alina@demo.by", password="demo1234", expected_role="moderator"),
    ]:
        assert client.post(API + "/auth/login", json=body).status_code == 401
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "alina@demo.by"))
        token = create_access_token(user.id, expires_delta=timedelta(seconds=-1))
    assert (
        client.get(
            API + "/auth/me", headers={"Authorization": "Bearer " + token}
        ).status_code
        == 401
    )
    assert (
        client.get(
            API + "/events", headers={"Authorization": "Bearer garbage"}
        ).status_code
        == 401
    )
    token = auth("alina")
    with SessionLocal.begin() as db:
        db.scalar(select(User).where(User.email == "alina@demo.by")).is_active = False
    assert client.get(API + "/auth/me", headers=token).status_code == 401


def test_signup_is_atomic_and_does_not_claim_existing_child(client):
    school = client.get(API + "/organizations?kind=school").json()["items"][0]["id"]
    data = dict(
        role="student",
        first_name="Алина",
        last_name="Коваль",
        birth_date="2010-04-12",
        school_id=school,
        email="NEW@example.org",
        password="password123",
    )
    response = client.post(API + "/auth/register", json=data)
    assert response.status_code == 201, response.text
    assert response.json()["user"]["email"] == "new@example.org"
    assert response.json()["user"]["profile_complete"] is False
    with SessionLocal() as db:
        old = db.scalar(select(User).where(User.email == "alina@demo.by"))
        assert str(old.id) != response.json()["user"]["id"]
    assert client.post(API + "/auth/register", json=data).status_code == 409
    for role in ("moderator", "school", "company"):
        assert (
            client.post(API + "/auth/register", json={**data, "role": role}).status_code
            == 422
        )
    assert (
        client.post(
            API + "/auth/register",
            json={
                **data,
                "school_id": "00000000-0000-0000-0000-000000000000",
                "email": "unused@example.org",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            API + "/auth/register",
            json=dict(
                role="parent",
                first_name="Иван",
                last_name="Коваль",
                email="parent@example.org",
                password="password123",
            ),
        ).status_code
        == 201
    )


def test_system_and_cors(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    for path in ("/not-a-page", "/assets/missing.js", "/api/v1/unknown"):
        r = client.get(path)
        assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    response = client.options(
        API + "/auth/me",
        headers={
            "Origin": "http://frontend.test",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://frontend.test"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert (
        "access-control-allow-origin"
        not in client.options(
            API + "/auth/me",
            headers={
                "Origin": "http://other.test",
                "Access-Control-Request-Method": "GET",
            },
        ).headers
    )


def test_password_whitespace_is_preserved(client):
    data = dict(
        role="parent",
        first_name="Тест",
        last_name="Пароль",
        email="spaces@example.org",
        password=" password123 ",
    )
    registered = client.post(API + "/auth/register", json=data)
    assert registered.status_code == 201
    assert (
        client.post(
            API + "/auth/login", json=dict(email=data["email"], password="password123")
        ).status_code
        == 401
    )
    assert (
        client.post(
            API + "/auth/login",
            json=dict(email=data["email"], password=data["password"]),
        ).status_code
        == 200
    )


def test_cors_allows_any_origin_when_wildcard_configured(monkeypatch):
    from fastapi.testclient import TestClient
    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setattr(get_settings(), "trusted_origins", "*")
    with TestClient(create_app()) as public_client:
        response = public_client.options(
            API + "/auth/me",
            headers={
                "Origin": "https://new-frontend.example.org",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
