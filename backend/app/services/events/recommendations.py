from sqlalchemy import select

from app.models import Event, EventRegistration, StudentProfile
from app.services.events.views import event_view
from app.services.shared.text import normalize
from app.services.shared.time import today


def recommendation_cards(db, user, interest=None):
    wanted = (
        {normalize(i) for i in interest}
        if interest is not None
        else {i.normalized_name for i in db.get(StudentProfile, user.id).interests}
    )
    if not wanted:
        return dict(items=[])
    statuses = {
        r.event_id: r.status
        for r in db.scalars(
            select(EventRegistration).where(
                EventRegistration.student_user_id == user.id
            )
        )
    }
    events = db.scalars(
        select(Event)
        .where(
            Event.status == "published",
            Event.registration_deadline >= today(),
            Event.event_date >= today(),
        )
        .order_by(Event.event_date, Event.id)
    )
    return dict(
        items=[
            event_view(db, e, user)
            for e in events
            if statuses.get(e.id) in (None, "cancelled")
            and wanted.intersection(i.normalized_name for i in e.interests)
        ][:3]
    )
