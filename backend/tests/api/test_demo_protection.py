from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.demo import demo_id
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import (
    Event, EventRegistration, Organization, PartnershipRequest, PartnershipResponse, User,
)
from app.schemas.events.responses import EventOut
from app.schemas.partnerships.responses import PartnershipOut, PartnershipResponseOut
from app.schemas.registrations.responses import RegistrationOut
from tests.api.test_events import payload

API = "/api/v1"


def snapshot():
    with SessionLocal() as db:
        return {
            table.name: sorted(repr(tuple(row)) for row in db.execute(select(table)))
            for table in Base.metadata.sorted_tables
        }


@pytest.mark.parametrize("persona", ["school", "school2", "company", "academy"])
def test_organizer_writes_are_contract_valid_and_leave_entire_database_unchanged(client, auth, persona):
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:" + persona))
        other = demo_id("org:company" if user.role == "school" else "org:school")
        values = {**payload(), "capacity": 40}
        from app.schemas.events.requests import EventCreate
        event = Event(**EventCreate(**values).model_dump(exclude={"interests"}),
                      organizer_id=user.organization_id, status="published")
        closed = Event(**EventCreate(**values).model_dump(exclude={"interests"}),
                       organizer_id=user.organization_id, status="registration_closed")
        db.add_all([event, closed])
        db.flush()
        submitted = EventRegistration(event_id=event.id, student_user_id=demo_id("user:alina"), status="submitted")
        approved = EventRegistration(event_id=event.id, student_user_id=demo_id("user:ilya"), status="approved")
        inbound = PartnershipRequest(sender_org_id=other, target_org_id=user.organization_id,
                                     visibility="direct", title="Входящий запрос", description="Программа",
                                     moderation_status="approved")
        market = PartnershipRequest(sender_org_id=other,
                                    visibility="all_schools" if user.role == "school" else "all_companies",
                                    title="Открытая программа", description="Программа", moderation_status="approved")
        outbound = PartnershipRequest(sender_org_id=user.organization_id,
                                      visibility="all_companies" if user.role == "school" else "all_schools",
                                      title="Наша программа", description="Программа", moderation_status="approved")
        db.add_all([submitted, approved, inbound, market, outbound])
        db.flush()
        response = PartnershipResponse(request_id=outbound.id, responder_org_id=other, status="pending")
        db.add(response)
        db.flush()
        event_id, closed_id, sub_id, app_id = event.id, closed.id, submitted.id, approved.id
        inbound_id, market_id, response_id = inbound.id, market.id, response.id
    headers = auth(persona)
    before = snapshot()
    operations = [
        ("post", "/events", {**payload(), "interests": ["Совершенно новое направление"]}),
        ("post", f"/events/{event_id}/close-registration", None),
        ("post", f"/events/{closed_id}/open-registration", None),
        ("post", f"/events/{event_id}/complete", None),
        ("patch", f"/registrations/{sub_id}/decision", {"decision": "approved"}),
        ("patch", f"/registrations/{sub_id}/decision", {"decision": "rejected"}),
        ("put", f"/registrations/{app_id}/attendance", None),
        ("post", "/partnership-requests", dict(visibility="direct", target_org_id=str(other), title="Новая программа", description="Описание")),
        ("patch", f"/partnership-requests/{inbound_id}/decision", {"decision": "accepted"}),
        ("post", f"/partnership-requests/{market_id}/responses", None),
        ("patch", f"/partnership-responses/{response_id}/decision", {"decision": "accepted"}),
    ]
    for method, path, body in operations:
        result = getattr(client, method)(API + path, headers=headers, **({"json": body} if body is not None else {}))
        assert result.status_code == 200
        assert result.json() == {"demo_mode": True}
        assert snapshot() == before

    # Existing permission and input checks still run, even for previews.
    assert client.post(API + "/events", headers=headers, json={}).status_code == 422
    assert client.post(API + f"/events/{uuid4()}/complete", headers=headers).status_code == 404
    assert client.post(API + f"/events/{demo_id('event:presenter-school-open')}/complete",
                       headers=headers).status_code == 404
    assert client.post(API + "/partnership-requests", headers=headers,
                       json=dict(visibility="direct", target_org_id=str(user.organization_id),
                                 title="Неверная цель", description="Описание")).status_code == 422
    assert snapshot() == before


def test_moderator_previews_never_create_accounts_publish_content_or_rotate_access(client, auth):
    headers = auth("admin")
    before = snapshot()
    for resource, identity in (
        ("events", demo_id("event:pending-company")),
        ("partnership-requests", demo_id("partnership:pending")),
        ("achievements", demo_id("achievement:pending")),
    ):
        for decision in ("approve", "reject"):
            result = client.post(API + f"/moderation/{resource}/{identity}/decision",
                                 headers=headers, json={"decision": decision})
            assert result.status_code == 200, result.text
            assert result.json() == {"demo_mode": True}
    for kind in ("school", "company", "academy"):
        result = client.post(API + "/moderation/organization-accounts", headers=headers, json={
            "organization": {"kind": kind, "name": "Временная организация", "city": "Минск"},
            "first_name": "Имя", "last_name": "Фамилия", "email": "preview@example.org",
        })
        assert result.status_code == 200
        assert result.json() == {"demo_mode": True}
    for persona in ("school", "school2", "company", "academy", "presenter-school", "presenter-company"):
        result = client.post(API + f"/moderation/organization-accounts/{demo_id('user:' + persona)}/token", headers=headers)
        assert result.status_code == 200
        assert result.json() == {"demo_mode": True}
    assert snapshot() == before


def test_unknown_write_endpoint_is_denied_globally_and_identity_survives_role_changes(client, auth):
    from app.main import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    calls = []

    @app.post("/api/v1/future-write")
    def future_write():
        calls.append(True)
        return {"ok": True}

    headers = auth("company")
    with TestClient(app) as future:
        for persona in ("school", "school2", "company", "academy", "admin"):
            assert future.post(API + "/future-write", headers=auth(persona)).json() == {"demo_mode": True}
        assert not calls
        assert future.post(API + "/future-write", headers=auth("writer-company")).status_code == 200
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:company"))
        user.email = "renamed@example.org"
        user.role = "parent"
        user.organization_id = None
    assert client.post(API + "/parents/me/invitation", headers=headers).json() == {"demo_mode": True}
    assert client.get(API + "/auth/me", headers=headers).status_code == 200


def test_mutation_metadata_and_openapi(client, auth):
    student = auth("alina")
    result = client.patch(API + "/students/me", headers=student, json={"city": "Минск", "grade": 10, "interests": ["Физика"]})
    assert result.status_code == 200
    assert result.json()["demo_mode"] is False
    assert "demo_mode" not in client.get(API + "/students/me", headers=student).json()
    assert "demo_mode" not in client.get(API + "/auth/me", headers=student).json()
    schema = client.get("/openapi.json").json()
    assert "anyOf" in schema["paths"][API + "/events"]["post"]["responses"]["200"]["content"]["application/json"]["schema"] or schema["paths"][API + "/events"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["demo_mode"]["const"] is True
