from datetime import datetime
from uuid import UUID

from app.schemas.shared.base import Output


class AttendanceOut(Output):
    id: UUID
    event_id: UUID
    title: str
    attended_at: datetime


class AchievementOut(Output):
    id: UUID
    title: str
    event_id: UUID | None
