from datetime import datetime
from typing import Literal
from uuid import UUID

from app.schemas.shared.base import Items, Output


class NotificationOut(Output):
    id: UUID
    type: Literal["confirmation", "deadline", "interest", "invite"]
    title: str
    body: str
    event_id: UUID | None
    created_at: datetime
    read: bool


class FeedOut(Items[NotificationOut]):
    unread_count: int
