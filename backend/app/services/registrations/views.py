from sqlalchemy import select

from app.models import (
    Event,
    EventRegistration,
)
from app.schemas.registrations.responses import RegistrationBrief
from app.services.events.views import brief_event


def registrations(db, identity):
    return list(
        db.scalars(
            select(EventRegistration)
            .where(EventRegistration.student_user_id == identity)
            .order_by(EventRegistration.created_at.desc(), EventRegistration.id)
        )
    )


def registration_view(db, r):
    return dict(
        **RegistrationBrief.model_validate(r).model_dump(),
        event=brief_event(db, db.get(Event, r.event_id)),
    )
