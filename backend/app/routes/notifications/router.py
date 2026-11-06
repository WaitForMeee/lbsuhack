from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.errors import fail
from app.models import Notification
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Student
from app.schemas.notifications.responses import FeedOut, NotificationOut
from app.services.shared.repository import get

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


@router.put("/notifications/{identity}/read", response_model=NotificationOut)
def read_notification(identity: UUID, db: DB, user: Student):
    item = get(db, Notification, identity, lock=True)
    if item.student_user_id != user.id:
        fail(404, "not_found", "Уведомление не найдено")
    if item.read_at is None:
        item.read_at = now()
        db.commit()
    return dict(
        id=item.id,
        type=item.type,
        title=item.title,
        body=item.body,
        event_id=item.event_id,
        created_at=item.created_at,
        read=True,
    )
