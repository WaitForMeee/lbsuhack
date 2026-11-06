from sqlalchemy import select

from app.models import (
    Achievement,
    Event,
)
from app.services.registrations.views import registrations


def success_view(db, identity):
    return dict(
        attendances=[
            dict(
                id=r.id,
                event_id=r.event_id,
                title=db.get(Event, r.event_id).title,
                attended_at=r.attended_at,
            )
            for r in registrations(db, identity)
            if r.attended_at
        ],
        achievements=[
            dict(id=a.id, title=a.title, event_id=a.event_id)
            for a in db.scalars(
                select(Achievement)
                .where(
                    Achievement.student_user_id == identity,
                    Achievement.status == "confirmed",
                )
                .order_by(Achievement.created_at.desc(), Achievement.id)
            )
        ],
    )
