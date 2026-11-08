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
            owner = db.get(User, demo_id("user:writer-company"))
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
                    demo_id("user:alina" if operation == "apply" else "user:writer-school"),
                )
                barrier.wait(timeout=10)
                if operation == "apply":
                    return apply(db, demo_id("event:junior"), user)[0].id
                return respond(db, demo_id("partnership:market"), user).id

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
            assert results[0] == results[1]


def test_invitation_creation_and_acceptance_are_serialized():
    from app.routes.parents.router import create_invitation
    from app.services.parents.invitations import accept_invitation
    from app.models import FamilyInvitation, ParentChild

    barrier = Barrier(2)
    def create(_):
        with SessionLocal() as db:
            parent = db.get(User, demo_id("user:olga"))
            barrier.wait(timeout=10)
            return create_invitation(db, parent)["invitation"]["token"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        tokens = list(pool.map(create, range(2)))
    assert tokens[0] == tokens[1]
    barrier = Barrier(2)
    def accept(_):
        with SessionLocal() as db:
            student = db.get(User, demo_id("user:mark"))
            barrier.wait(timeout=10)
            return accept_invitation(db, student, tokens[0])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(accept, range(2)))
    assert sorted(r["already_joined"] for r in results) == [False, True]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(FamilyInvitation)) == 1
        assert db.get(ParentChild, (demo_id("user:olga"), demo_id("user:mark"))) is not None


def test_accept_and_delete_invitation_have_a_serial_order():
    from app.routes.parents.router import create_invitation, delete_invitation
    from app.services.parents.invitations import accept_invitation
    from app.models import FamilyInvitation, ParentChild

    with SessionLocal() as db:
        token = create_invitation(db, db.get(User, demo_id("user:olga")))["invitation"]["token"]
    barrier = Barrier(2)
    def operation(kind):
        with SessionLocal() as db:
            person = db.get(User, demo_id("user:olga" if kind == "delete" else "mark"))
            barrier.wait(timeout=10)
            if kind == "delete":
                delete_invitation(db, person)
                return 200
            try:
                accept_invitation(db, person, token)
                return 200
            except HTTPException as error:
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted, deleted = list(pool.map(operation, ("accept", "delete")))
    assert deleted == 200 and accepted in (200, 404)
    with SessionLocal() as db:
        assert db.get(FamilyInvitation, demo_id("user:olga")) is None
        assert (db.get(ParentChild, (demo_id("user:olga"), demo_id("user:mark"))) is not None) == (accepted == 200)
