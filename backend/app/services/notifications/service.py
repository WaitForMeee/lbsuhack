from sqlalchemy import select

from app.models import Notification


def notify(db, *, student_id, event_id, type, title, body, key):
    if db.scalar(select(Notification.id).where(Notification.source_key == key)) is None:
        db.add(
            Notification(
                student_user_id=student_id,
                event_id=event_id,
                type=type,
                title=title,
                body=body,
                source_key=key,
            )
        )
