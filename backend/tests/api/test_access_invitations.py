import pytest
from sqlalchemy import select, func

from app.db.session import SessionLocal
from app.models import FamilyInvitation, Organization, ParentChild, User
from app.scripts.seed_demo import DEMO_ORGANIZATION_TOKENS, demo_id, seed_demo

API = "/api/v1"


def create_parent(client, email="another.parent@example.org"):
    session = client.post(API + "/auth/register", json=dict(role="parent", first_name="Новый", last_name="Родитель", email=email, password="password123"))
    assert session.status_code == 201, session.text
    return {"Authorization": "Bearer " + session.json()["access_token"]}


def test_family_invitation_lifecycle_and_multiple_parents(client, auth):
    parent = auth("olga")
    assert client.get(API + "/parents/me/invitation", headers=parent).json() == {"invitation": None}
    token = client.post(API + "/parents/me/invitation", headers=parent).json()["invitation"]["token"]
    assert client.get(API + "/parents/me/invitation", headers=parent).json()["invitation"]["token"] == token
    assert client.post(API + "/parents/me/invitation", headers=parent).json()["invitation"]["token"] == token
    for who in ("mark", "ilya", "mark"):
        response = client.post(API + "/family-invitations/accept", json={"token": token}, headers=auth(who))
        assert response.status_code == 200, response.text
    children = client.get(API + "/parents/me/children", headers=parent).json()
    assert len(children["items"]) == 3
    assert children["active_child_id"] == str(demo_id("user:alina"))
    assert client.post(API + "/family-invitations/accept", json={"token": token}, headers=auth("mark")).json()["already_joined"] is True
    second = create_parent(client)
    other = client.post(API + "/parents/me/invitation", headers=second).json()["invitation"]["token"]
    assert client.post(API + "/family-invitations/accept", json={"token": other}, headers=auth("mark")).status_code == 200
    assert client.get(API + "/parents/me/children", headers=second).json()["active_child_id"] == str(demo_id("user:mark"))
    assert client.delete(API + "/parents/me/invitation", headers=parent).status_code == 200
    assert client.delete(API + "/parents/me/invitation", headers=parent).status_code == 200
    assert client.post(API + "/family-invitations/accept", json={"token": token}, headers=auth("maria")).status_code == 404
    new = client.post(API + "/parents/me/invitation", headers=parent).json()["invitation"]["token"]
    assert new != token
    assert len(client.get(API + "/parents/me/children", headers=parent).json()["items"]) == 3


def test_invitation_permissions_and_token_purposes(client, auth):
    token = client.post(API + "/parents/me/invitation", headers=auth("olga")).json()["invitation"]["token"]
    for method in (client.get, client.post, client.delete):
        assert method(API + "/parents/me/invitation").status_code == 401
        for who in ("alina", "school", "company", "admin"):
            assert method(API + "/parents/me/invitation", headers=auth(who)).status_code == 403
    assert client.post(API + "/family-invitations/accept", json={"token": token}).status_code == 401
    for who in ("olga", "school", "company", "admin"):
        assert client.post(API + "/family-invitations/accept", json={"token": token}, headers=auth(who)).status_code == 403
    for bad in ("bad", auth("alina")["Authorization"].split()[1], token[:-8] + "abcdefgh"):
        assert client.post(API + "/family-invitations/accept", json={"token": bad}, headers=auth("alina")).status_code == 404
    assert client.get(API + "/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401
    assert client.get(API + "/family-invitations/accept").status_code == 405


@pytest.mark.parametrize("kind,role", [("school", "school"), ("company", "company"), ("academy", "company")])
def test_moderator_create_login_rotate_and_preserve_seed(client, auth, kind, role):
    moderator = auth("writer-admin")
    payload = dict(organization=dict(kind=kind, name="Новая организация", city="Минск"), first_name="Иван", last_name="Иванов", email="created@example.org")
    created = client.post(API + "/moderation/organization-accounts", headers=moderator, json=payload)
    assert created.status_code == 201, created.text
    data = created.json()
    identity, token = data["account"]["user"]["id"], data["token"]
    assert data["account"]["user"]["role"] == role
    assert "password" not in str(data) and "token_hash" not in str(data)
    listed = client.get(API + "/moderation/organization-accounts", headers=moderator).json()
    assert token not in str(listed)
    login = client.post(API + "/auth/organization-login", json={"token": token, "expected_role": role})
    assert login.status_code == 200, login.text
    old_session = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get(API + "/organizations/me/dashboard", headers=old_session).status_code == 200
    assert client.post(API + "/auth/organization-login", json={"token": token, "expected_role": "company" if role == "school" else "school"}).status_code == 401
    rotated = client.post(API + f"/moderation/organization-accounts/{identity}/token", headers=moderator)
    assert rotated.status_code == 200
    new_token = rotated.json()["token"]
    assert token != new_token
    assert client.get(API + "/auth/me", headers=old_session).status_code == 401
    assert client.post(API + "/auth/organization-login", json={"token": token}).status_code == 401
    assert client.post(API + "/auth/organization-login", json={"token": new_token}).status_code == 200
    assert client.post(API + "/auth/login", json={"email": payload["email"], "password": "demo1234"}).status_code == 401
    with SessionLocal.begin() as db:
        seed_demo(db)
    assert client.post(API + "/auth/organization-login", json={"token": new_token}).status_code == 200


def test_account_permissions_atomic_creation_and_existing_organization(client, auth):
    path = API + "/moderation/organization-accounts"
    payload = dict(organization=dict(kind="school", name="Не создавать", city="Минск"), first_name="Имя", last_name="Фамилия", email="admin@demo.by")
    assert client.get(path).status_code == 401
    for who in ("alina", "olga", "school", "company"):
        assert client.get(path, headers=auth(who)).status_code == 403
        assert client.post(path, json=payload, headers=auth(who)).status_code == 403
        assert client.post(path + f"/{demo_id('user:school')}/token", headers=auth(who)).status_code == 403
    moderator = auth("writer-admin")
    assert client.post(path, json=payload, headers=moderator).status_code == 409
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Organization).where(Organization.name == "Не создавать")) == 0
    del payload["organization"]
    payload.update(organization_id=str(demo_id("org:school")), email="another.representative@example.org")
    assert client.post(path, json=payload, headers=moderator).status_code == 201
    assert client.post(path + f"/{demo_id('user:alina')}/token", headers=moderator).status_code == 404
    for who in ("school", "company"):
        assert client.post(API + "/auth/login", json={"email": who + "@demo.by", "password": "demo1234"}).status_code == 401
    assert client.post(API + "/auth/organization-login", json={"token": "invalid"}).status_code == 401
    with SessionLocal.begin() as db:
        db.get(User, demo_id("user:school")).is_active = False
    assert client.post(API + "/auth/organization-login", json={"token": DEMO_ORGANIZATION_TOKENS["school"]}).status_code == 401


def test_demo_seed_preserves_rotated_credentials_and_cors_delete(client, auth):
    rotated = client.post(API + f"/moderation/organization-accounts/{demo_id('user:school')}/token", headers=auth("writer-admin"))
    assert rotated.status_code == 200
    token = rotated.json()["token"]
    assert rotated.headers["cache-control"] == "no-store"
    with SessionLocal.begin() as db:
        seed_demo(db)
    assert client.post(API + "/auth/organization-login", json={"token": token}).status_code == 200
    assert client.post(API + "/auth/organization-login", json={"token": DEMO_ORGANIZATION_TOKENS["school"]}).status_code == 401
    response = client.options(API + "/parents/me/invitation", headers={"Origin": "http://frontend.test", "Access-Control-Request-Method": "DELETE", "Access-Control-Request-Headers": "Authorization"})
    assert response.status_code == 200
