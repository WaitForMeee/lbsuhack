from datetime import timedelta

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.users.user import User


TRUSTED_ORIGIN = {"Origin": "http://localhost:5173"}


def login(client):
    return client.post(
        "/api/v1/auth/login",
        json={"email": "student@talenthub.by", "password": "student-password"},
        headers=TRUSTED_ORIGIN,
    )


def test_login_me_and_logout(client):
    response = login(client)
    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert get_settings().auth_cookie_name in response.cookies

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "student@talenthub.by"

    logout_response = client.post("/api/v1/auth/logout", headers=TRUSTED_ORIGIN)
    assert logout_response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_password_is_hashed_and_invalid_login_is_rejected(client):
    with SessionLocal() as session:
        user = session.query(User).filter_by(email="student@talenthub.by").one()
        assert user.password_hash != "student-password"
        assert user.password_hash.startswith("$argon2")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@talenthub.by", "password": "wrong-password"},
        headers=TRUSTED_ORIGIN,
    )
    assert response.status_code == 401


def test_expired_and_tampered_tokens_are_rejected(client):
    with SessionLocal() as session:
        user = session.query(User).one()
        expired = create_access_token(user.id, expires_delta=timedelta(seconds=-1))

    cookie_name = get_settings().auth_cookie_name
    client.cookies.set(cookie_name, expired)
    assert client.get("/api/v1/auth/me").status_code == 401

    client.cookies.set(cookie_name, expired + "tampered")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_untrusted_origin_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@talenthub.by", "password": "student-password"},
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403


def test_health_and_unknown_routes(client):
    assert client.get("/health").json() == {"status": "ok"}
    account_response = client.get("/account")
    assert account_response.status_code == 200
    assert "TalentHub" in account_response.text
    assert client.get("/api/v1/unknown").status_code == 404
    assert client.get("/missing.js").status_code == 404
