from sqlalchemy import select

from app.core.demo import demo_id
from app.db.session import SessionLocal
from app.models import Event, EventRegistration, FamilyInvitation, Notification, ParentChild, ParentLink, User
from app.scripts.reset_demo import reset_demo
from app.scripts.reset_presenter_credentials import reset_presenter_credentials
from app.scripts.seed_demo import seed_demo
from tests.api.test_events import payload

API = "/api/v1"


def login(client, credential):
    organization = credential["method"] == "organization_token"
    response = client.post(
        API + ("/auth/organization-login" if organization else "/auth/login"),
        json={"token": credential["secret"]} if organization else {
            "email": credential["email"], "password": credential["secret"],
        },
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def credentials_snapshot():
    with SessionLocal() as db:
        return {
            user.id: (user.email, user.password_hash, user.organization_token_hash, user.credential_version)
            for user in db.scalars(select(User))
        }


def test_private_accounts_are_filled_writable_and_family_invitation_uses_student_jwt(client, reset_database):
    credentials = {row["email"].split("@")[0]: row for row in reset_database}
    assert len(credentials) == 6
    headers = {key: login(client, row) for key, row in credentials.items()}
    for index in (1, 2):
        student = headers[f"presenter-child{index}"]
        assert client.get(API + "/auth/me", headers=student).json()["profile_complete"]
        assert len(client.get(API + "/registrations/me", headers=student).json()["items"]) == 4
        success = client.get(API + "/students/me/success", headers=student).json()
        assert success["achievements"]
        notifications = client.get(API + "/notifications/me", headers=student).json()["items"]
        assert any(not n["read"] for n in notifications)
        assert any(n["read"] for n in notifications)
    parent = headers["presenter-parent"]
    children = client.get(API + "/parents/me/children", headers=parent).json()
    assert len(children["items"]) == 1
    assert children["active_child_id"] == str(demo_id("user:presenter-child1"))
    invitation = client.post(API + "/parents/me/invitation", headers=parent).json()["invitation"]["token"]
    path = API + "/family-invitations/accept"
    joined = client.post(path, headers=headers["presenter-child2"], json={"token": invitation})
    assert joined.status_code == 200 and joined.json()["already_joined"] is False
    assert client.post(path, headers=headers["presenter-child2"], json={"token": invitation}).json()["already_joined"]
    with SessionLocal.begin() as db:
        result = seed_demo(db)
        assert result["credentials"] == []
    assert len(client.get(API + "/parents/me/children", headers=parent).json()["items"]) == 2

    for key in ("presenter-school", "presenter-company"):
        created = client.post(API + "/events", headers=headers[key], json=payload())
        assert created.status_code == 201
        event = created.json()
        reviewed = client.post(API + f"/moderation/events/{event['id']}/decision",
                               headers=headers["presenter-admin"], json={"decision": "approve"})
        assert reviewed.status_code == 200 and reviewed.json()["status"] == "published"
        assert client.get(API + "/events/" + event["id"]).status_code == 200


def test_reset_restores_both_datasets_preserves_credentials_and_unrelated_records(client, reset_database):
    credentials = reset_database
    original = credentials_snapshot()
    with SessionLocal.begin() as db:
        parent, second = demo_id("user:presenter-parent"), demo_id("user:presenter-child2")
        db.add(ParentChild(parent_user_id=parent, student_user_id=second))
        db.get(ParentLink, parent).student_user_id = second
        db.add(FamilyInvitation(parent_user_id=parent))
        db.get(User, demo_id("user:presenter-child1")).first_name = "Изменено"
        db.get(Event, demo_id("event:presenter-school-open")).status = "completed"
        db.get(EventRegistration, demo_id("registration:presenter-1-school-open")).status = "rejected"
        db.get(Notification, demo_id("notification:presenter-1-confirmation")).title = "Изменено"
    with SessionLocal.begin() as db:
        assert reset_demo(db)["credentials"] == []
    assert credentials_snapshot() == original
    for row in credentials:
        login(client, row)
    with SessionLocal() as db:
        parent = demo_id("user:presenter-parent")
        assert db.get(ParentChild, (parent, demo_id("user:presenter-child2"))) is None
        assert db.get(ParentLink, parent).student_user_id == demo_id("user:presenter-child1")
        assert db.get(FamilyInvitation, parent) is None
        assert db.get(User, demo_id("user:presenter-child1")).first_name == "Алексей"
        assert db.get(Event, demo_id("event:presenter-school-open")).status == "published"
        assert db.get(EventRegistration, demo_id("registration:presenter-1-school-open")).status == "submitted"
        assert db.get(Notification, demo_id("notification:presenter-1-confirmation")).title == "Заявка рассмотрена"


def test_explicit_credential_rotation_preserves_data_and_prints_only_after_commit(client, reset_database, capsys):
    from app.scripts.presenter_demo import print_credentials
    from tests.api.test_demo_protection import snapshot

    old = reset_database
    old_sessions = {row["email"]: login(client, row) for row in old}
    before = snapshot()
    with SessionLocal.begin() as db:
        fresh = reset_presenter_credentials(db)
        assert capsys.readouterr().out == ""
    after = snapshot()
    assert {key: rows for key, rows in before.items() if key != "users"} == {
        key: rows for key, rows in after.items() if key != "users"
    }
    print_credentials(fresh)
    output = capsys.readouterr().out
    for row in fresh:
        assert row["secret"] in output
        login(client, row)
    for row in old:
        org = row["method"] == "organization_token"
        rejected = client.post(API + ("/auth/organization-login" if org else "/auth/login"),
                               json={"token": row["secret"]} if org else {
                                   "email": row["email"], "password": row["secret"],
                               })
        assert rejected.status_code == 401
        if org:
            assert client.get(API + "/auth/me", headers=old_sessions[row["email"]]).status_code == 401
    with SessionLocal.begin() as db:
        assert seed_demo(db)["credentials"] == []
    for row in fresh:
        login(client, row)
