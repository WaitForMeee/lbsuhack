from app.db.session import SessionLocal
from app.models import Notification, User
from app.scripts.seed_demo import demo_id
from sqlalchemy import func, select

API = "/api/v1"


def test_token_reads_current_role_and_organization(client, auth):
    headers = auth("company")
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:company"))
        user.organization_id = demo_id("org:academy")
    assert (
        client.get(
            API + "/events/" + str(demo_id("event:code")) + "/registrations",
            headers=headers,
        ).status_code
        == 404
    )
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:company"))
        user.role = "parent"
        user.organization_id = None
    assert (
        client.get(API + "/organizations/me/dashboard", headers=headers).status_code
        == 403
    )
    assert client.get(API + "/auth/me", headers=headers).json()["role"] == "parent"


def test_decision_notifications_repeat_and_reapplication_cycle(client, auth):
    event = API + "/events/" + str(demo_id("event:junior"))
    registration = client.post(event + "/registrations", headers=auth("alina")).json()
    path = API + "/registrations/" + registration["id"]
    for _ in range(2):
        assert (
            client.patch(
                path + "/decision",
                headers=auth("company"),
                json={"decision": "approved"},
            ).status_code
            == 200
        )
    assert client.post(path + "/cancel", headers=auth("alina")).status_code == 200
    assert (
        client.post(event + "/registrations", headers=auth("alina")).json()["id"]
        == registration["id"]
    )
    assert (
        client.patch(
            path + "/decision", headers=auth("company"), json={"decision": "rejected"}
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.event_id == demo_id("event:junior"),
                    Notification.type == "confirmation",
                )
            )
            == 2
        )
    assert (
        client.post(event + "/registrations", headers=auth("alina")).status_code == 409
    )


def test_openapi_response_schemas_and_role_examples(client):
    spec = client.get("/openapi.json").json()
    assert {
        item["role"] for item in spec["components"]["schemas"]["UserOut"]["examples"]
    } == {"student", "parent", "school", "company", "moderator"}
    for path, methods in spec["paths"].items():
        if not path.startswith(API):
            continue
        for operation in methods.values():
            successes = [
                r for code, r in operation["responses"].items() if code.startswith("2")
            ]
            assert successes and all(
                r["content"]["application/json"]["schema"] for r in successes
            )
    assert (
        client.get(
            API + "/events", headers={"Authorization": "Basic invalid"}
        ).status_code
        == 401
    )
