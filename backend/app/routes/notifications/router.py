from fastapi import APIRouter
from sqlalchemy import select

from app.models import Notification
from app.routes.shared.dependencies import DB, Student
from app.schemas.notifications.responses import FeedOut

router = APIRouter(tags=["notifications"])


@router.get("/notifications/me", response_model=FeedOut)
def feed(db: DB, user: Student):
    rows = list(
        db.scalars(
            select(Notification)
            .where(Notification.student_user_id == user.id)
            .order_by(Notification.created_at.desc(), Notification.id)
        )
    )
    return dict(
        items=[
            dict(
                id=n.id,
                type=n.type,
                title=n.title,
                body=n.body,
                event_id=n.event_id,
                created_at=n.created_at,
                read=n.read_at is not None,
            )
            for n in rows
        ],
        unread_count=sum(n.read_at is None for n in rows),
    )
