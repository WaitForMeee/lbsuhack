"""Regression coverage carried forward from the former mock seed/reset tests."""

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models import (
    Event,
    EventRegistration,
    Notification,
    ParentChild,
    ParentLink,
    User,
)
from app.scripts.reset_demo import reset_demo
from app.scripts.seed_demo import demo_id, seed_demo
from sqlalchemy import func, select


def test_seed_repeatable_preserves_passwords_profile_and_decisions():
    with SessionLocal.begin() as db:
        user = db.get(User, demo_id("user:alina"))
        original = user.password_hash
        user.first_name = "Своё имя"
        event = db.get(Event, demo_id("event:pending-company"))
        event.status = "rejected"
        event.description = "Изменённый текст"
        db.get(EventRegistration, demo_id("registration:code")).status = "cancelled"
        db.get(ParentLink, demo_id("user:olga")).student_user_id = demo_id("user:mark")
        db.add(
            ParentChild(
                parent_user_id=demo_id("user:olga"),
                student_user_id=demo_id("user:mark"),
            )
        )
    with SessionLocal.begin() as db:
        before = {
            m.__name__: db.scalar(select(func.count()).select_from(m))
            for m in (User, Event, EventRegistration, Notification)
        }
        seed_demo(db)
    with SessionLocal() as db:
        assert before == {
            m.__name__: db.scalar(select(func.count()).select_from(m))
            for m in (User, Event, EventRegistration, Notification)
        }
        user = db.get(User, demo_id("user:alina"))
        assert user.password_hash == original and user.first_name == "Своё имя"
        assert verify_password("demo1234", user.password_hash)
        event = db.get(Event, demo_id("event:pending-company"))
        assert event.status == "rejected" and event.description == "Изменённый текст"
        assert (
            db.get(EventRegistration, demo_id("registration:code")).status
            == "cancelled"
        )
        assert db.get(ParentLink, demo_id("user:olga")).student_user_id == demo_id(
            "user:mark"
        )
        assert (
            db.get(ParentChild, (demo_id("user:olga"), demo_id("user:alina")))
            is not None
        )
        assert db.scalar(select(func.count()).select_from(ParentChild)) == 3
        assert {n.type for n in db.scalars(select(Notification))} == {
            "confirmation",
            "interest",
            "deadline",
            "invite",
        }


def test_explicit_reset_restores_demo_and_preserves_unrelated_account():
    with SessionLocal.begin() as db:
        db.get(User, demo_id("user:alina")).first_name = "Изменено"
        db.add(
            User(
                email="custom@example.org",
                first_name="Свое",
                last_name="Имя",
                role="parent",
                password_hash="unused",
            )
        )
    with SessionLocal.begin() as db:
        reset_demo(db)
    with SessionLocal() as db:
        assert db.get(User, demo_id("user:alina")).first_name == "Алина"
        assert (
            db.scalar(select(User).where(User.email == "custom@example.org"))
            is not None
        )
        assert db.get(ParentLink, demo_id("user:olga")).student_user_id == demo_id(
            "user:alina"
        )
        assert (
            db.get(ParentChild, (demo_id("user:olga"), demo_id("user:alina")))
            is not None
        )
        assert db.scalar(select(func.count()).select_from(ParentChild)) == 2
        assert db.scalar(select(func.count()).select_from(Event)) == 23


def test_seed_school_marketplace_is_actionable_and_preserves_responses(client, auth):
    from app.models import PartnershipRequest, PartnershipResponse

    expected = {
        str(demo_id("partnership:school-market-mentors")),
        str(demo_id("partnership:school-market-lab")),
    }
    for persona in ("company", "academy"):
        market = client.get(
            "/api/v1/partnership-requests?view=marketplace", headers=auth("writer-" + persona)
        )
        assert market.status_code == 200
        cards = [p for p in market.json()["items"] if p["id"] in expected]
        assert len(cards) == 2
        assert all(
            p["visibility"] == "all_companies"
            and p["moderation_status"] == "approved"
            and p["my_response"] is None
            for p in cards
        )
    identity = str(demo_id("partnership:school-market-mentors"))
    response = client.post(
        f"/api/v1/partnership-requests/{identity}/responses", headers=auth("writer-company")
    )
    assert response.status_code == 201
    response_id = response.json()["id"]
    assert (
        client.patch(
            f"/api/v1/partnership-responses/{response_id}/decision",
            headers=auth("writer-school"),
            json={"decision": "accepted"},
        ).status_code
        == 200
    )
    with SessionLocal.begin() as db:
        seed_demo(db)
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(PartnershipRequest)
                .where(PartnershipRequest.visibility == "all_companies")
            )
            == 3
        )
        assert (
            db.scalar(
                select(PartnershipResponse.status).where(
                    PartnershipResponse.request_id
                    == demo_id("partnership:school-market-mentors")
                )
            )
            == "accepted"
        )
