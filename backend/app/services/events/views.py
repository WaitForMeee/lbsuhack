from sqlalchemy import select

from app.models import (
    EventRegistration,
)
from app.schemas.registrations.responses import RegistrationBrief
from app.services.organizations.views import org_view


def brief_event(db, e):
    return dict(
        id=e.id,
        title=e.title,
        event_date=e.event_date,
        city=e.city,
        kind=e.kind,
        format=e.format,
        status=e.status,
        organizer=org_view(db, e.organizer_id),
    )


def event_view(db, e, user=None):
    rows = list(
        db.scalars(select(EventRegistration).where(EventRegistration.event_id == e.id))
    )
    mine = next((r for r in rows if user and r.student_user_id == user.id), None)
    return dict(
        id=e.id,
        organizer=org_view(db, e.organizer_id),
        title=e.title,
        description=e.description,
        kind=e.kind,
        project_kind=e.project_kind,
        interests=sorted(i.name for i in e.interests),
        grade_min=e.grade_min,
        grade_max=e.grade_max,
        event_date=e.event_date,
        registration_deadline=e.registration_deadline,
        city=e.city,
        venue=e.venue,
        format=e.format,
        terms=e.terms,
        capacity=e.capacity,
        status=e.status,
        created_at=e.created_at,
        places_remaining=max(0, e.capacity - sum(r.status == "approved" for r in rows)),
        registration_count=sum(r.status != "cancelled" for r in rows),
        my_registration=RegistrationBrief.model_validate(mine).model_dump()
        if mine
        else None,
    )
