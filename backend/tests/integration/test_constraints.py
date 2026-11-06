from datetime import timedelta

import pytest
from app.db.session import SessionLocal
from app.models import Event, EventRegistration, PartnershipResponse
from app.scripts.seed_demo import demo_id
from app.services.shared.time import today
from sqlalchemy.exc import IntegrityError


@pytest.mark.parametrize(
    "values",
    [
        {"capacity": 0},
        {"grade_min": 6},
        {"grade_min": 11, "grade_max": 10},
        {"registration_deadline": today() + timedelta(days=1000)},
    ],
)
def test_database_enforces_event_invariants(values):
    with SessionLocal() as db:
        event = db.get(Event, demo_id("event:math"))
        for key, value in values.items():
            setattr(event, key, value)
        with pytest.raises(IntegrityError):
            db.commit()


def test_database_rejects_duplicate_application_and_response():
    with SessionLocal() as db:
        db.add(
            EventRegistration(
                event_id=demo_id("event:math"), student_user_id=demo_id("user:alina")
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
    with SessionLocal.begin() as db:
        db.add(
            PartnershipResponse(
                request_id=demo_id("partnership:market"),
                school_id=demo_id("org:school"),
            )
        )
    with SessionLocal() as db:
        db.add(
            PartnershipResponse(
                request_id=demo_id("partnership:market"),
                school_id=demo_id("org:school"),
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
