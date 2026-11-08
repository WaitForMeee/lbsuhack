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
    create = client.post(API + "/events", headers=headers,
                         json={**payload(), "interests": ["Совершенно новое направление"]})
    assert create.status_code == 201, create.text
    EventOut.model_validate(create.json())
    assert client.get(API + "/events/" + create.json()["id"], headers=headers).status_code == 404
    for identity, action, status in (
        (event_id, "close-registration", "published"),
        (closed_id, "open-registration", "registration_closed"),
        (event_id, "complete", "published"),
    ):
        result = client.post(API + f"/events/{identity}/{action}", headers=headers)
        assert result.status_code == 200, result.text
        EventOut.model_validate(result.json())
        assert result.json()["status"] == status
    for decision in ("approved", "rejected"):
        result = client.patch(API + f"/registrations/{sub_id}/decision", headers=headers,
                              json={"decision": decision})
        assert result.status_code == 200, result.text
        RegistrationOut.model_validate(result.json())
        assert result.json()["status"] == "submitted"
    result = client.put(API + f"/registrations/{app_id}/attendance", headers=headers)
    assert result.status_code == 200, result.text
    RegistrationOut.model_validate(result.json())
    assert result.json()["attended_at"] is None
    created = client.post(API + "/partnership-requests", headers=headers,
                          json=dict(visibility="direct", target_org_id=str(other),
                                    title="Новая программа", description="Описание"))
    assert created.status_code == 201, created.text
    PartnershipOut.model_validate(created.json())
    result = client.patch(API + f"/partnership-requests/{inbound_id}/decision", headers=headers,
                          json={"decision": "accepted"})
    assert result.status_code == 200, result.text
    assert result.json()["direct_decision"] is None
    result = client.post(API + f"/partnership-requests/{market_id}/responses", headers=headers)
    assert result.status_code == 201, result.text
    PartnershipResponseOut.model_validate(result.json())
    with SessionLocal() as db:
        assert db.get(PartnershipResponse, UUID(result.json()["id"])) is None
    result = client.patch(API + f"/partnership-responses/{response_id}/decision", headers=headers,
                          json={"decision": "accepted"})
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "pending"
    assert snapshot() == before
    with SessionLocal.begin() as db:
        existing = PartnershipResponse(request_id=market_id, responder_org_id=user.organization_id,
                                       status="pending")
        db.add(existing)
        db.flush()
        existing_id = str(existing.id)
    before = snapshot()
    repeated = client.post(API + f"/partnership-requests/{market_id}/responses", headers=headers)
    assert repeated.status_code == 201 and repeated.json()["id"] == existing_id

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
            body = result.json()
            assert body.get("status", body.get("moderation_status")) == "pending"
    for kind in ("school", "company", "academy"):
        result = client.post(API + "/moderation/organization-accounts", headers=headers, json={
            "organization": {"kind": kind, "name": "Временная организация", "city": "Минск"},
            "first_name": "Имя", "last_name": "Фамилия", "email": "preview@example.org",
        })
        assert result.status_code == 201, result.text
        body = result.json()
        assert client.post(API + "/auth/organization-login", json={"token": body["token"]}).status_code == 401
        with SessionLocal() as db:
            assert db.get(User, UUID(body["account"]["user"]["id"])) is None
            assert db.get(Organization, UUID(body["account"]["organization"]["id"])) is None
    result = client.post(API + "/moderation/organization-accounts", headers=headers, json={
        "organization_id": str(demo_id("org:school")),
        "first_name": "Имя", "last_name": "Фамилия", "email": "preview.existing@example.org",
    })
    assert result.status_code == 201, result.text
    assert client.post(API + "/auth/organization-login", json={"token": result.json()["token"]}).status_code == 401
    assert client.post(API + "/moderation/organization-accounts", headers=headers, json={
        "organization": {"kind": "school", "name": "Не создавать", "city": "Минск"},
        "first_name": "Имя", "last_name": "Фамилия", "email": "admin@demo.by",
    }).status_code == 409
    for persona in ("school", "school2", "company", "academy", "presenter-school", "presenter-company"):
        result = client.post(API + f"/moderation/organization-accounts/{demo_id('user:' + persona)}/token",
                             headers=headers)
        assert result.status_code == 200, result.text
        assert client.post(API + "/auth/organization-login", json={"token": result.json()["token"]}).status_code == 401
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
            assert future.post(API + "/future-write", headers=auth(persona)).status_code == 403
        assert not calls
        assert future.post(API + "/future-write", headers=auth("writer-company")).status_code == 200
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:company"))
        user.email = "renamed@example.org"
        user.role = "parent"
        user.organization_id = None
    assert client.post(API + "/parents/me/invitation", headers=headers).status_code == 403
    assert client.get(API + "/auth/me", headers=headers).status_code == 200
