from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.db.session import SessionLocal, engine
from app.models import Event, EventRegistration, Notification, User
from app.scripts.seed_demo import demo_id
from app.services.partnerships.service import respond
from app.services.registrations.service import apply, decide_registration
from fastapi import HTTPException
from sqlalchemy import func, select

pytestmark = pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="Row locking requires isolated PostgreSQL; set TALENTHUB_TEST_DATABASE_URL",
)


def test_last_place_is_serialized():
    with SessionLocal.begin() as db:
        event = db.get(Event, demo_id("event:junior"))
        event.capacity = 1
        rows = [
            EventRegistration(event_id=event.id, student_user_id=demo_id("user:" + key))
            for key in ("alina", "ilya")
        ]
        db.add_all(rows)
        db.flush()
        identities = [r.id for r in rows]
    barrier = Barrier(2)

    def decide(identity):
        with SessionLocal() as db:
            owner = db.get(User, demo_id("user:company"))
            barrier.wait(timeout=10)
            try:
                decide_registration(db, identity, owner, "approved")
                return 200
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(decide, identities)) == [200, 409]
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(EventRegistration)
                .where(
                    EventRegistration.id.in_(identities),
                    EventRegistration.status == "approved",
                )
            )
            == 1
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.event_id == demo_id("event:junior"),
                    Notification.type == "confirmation",
                )
            )
            == 1
        )


def test_concurrent_apply_and_response_are_unique():
    for operation in ("apply", "respond"):
        barrier = Barrier(2)

        def run(_):
            with SessionLocal() as db:
                user = db.get(
                    User,
                    demo_id("user:alina" if operation == "apply" else "user:school"),
                )
                barrier.wait(timeout=10)
                if operation == "apply":
                    return apply(db, demo_id("event:junior"), user)[0].id
                return respond(db, demo_id("partnership:market"), user).id

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
            assert results[0] == results[1]
