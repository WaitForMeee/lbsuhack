from datetime import datetime
from uuid import UUID

from app.schemas.events.summary import EventBrief
from app.schemas.shared.base import Output
from app.schemas.shared.types import RegistrationStatus


class RegistrationBrief(Output):
    id: UUID
    event_id: UUID
    student_user_id: UUID
    status: RegistrationStatus
    attended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RegistrationOut(RegistrationBrief):
    event: EventBrief


class ParticipantOut(RegistrationOut):
    first_name: str
    last_name: str
    grade: int | None
    student_user_id: UUID
