"""Regression coverage carried forward from the former mock seed/reset tests."""

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models import Event, EventRegistration, Notification, ParentLink, User
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
        db.add(ParentLink(parent_user_id=demo_id("user:olga"), student_user_id=user.id))
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
        assert db.get(ParentLink, demo_id("user:olga")) is not None
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
        assert db.get(ParentLink, demo_id("user:olga")) is None
        assert db.scalar(select(func.count()).select_from(Event)) == 17
