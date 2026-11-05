from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.registrations.registration import RegistrationStatus


class RegistrationRead(BaseModel):
    id: UUID
    event_id: UUID
    event_slug: str
    event_title: str
    event_image_url: str | None
    event_starts_at: datetime
    organizer_name: str
    student_id: UUID
    student_name: str
    student_email: str
    status: RegistrationStatus
    created_at: datetime


class RegistrationStatusUpdate(BaseModel):
    status: RegistrationStatus
