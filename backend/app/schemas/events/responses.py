from datetime import date, datetime
from typing import Literal
from uuid import UUID

from app.schemas.organizations.responses import OrganizationOut
from app.schemas.registrations.responses import RegistrationBrief
from app.schemas.shared.base import Output
from app.schemas.shared.types import Kind


class EventOut(Output):
    id: UUID
    organizer: OrganizationOut
    title: str
    description: str
    kind: Kind
    project_kind: str | None
    interests: list[str]
    grade_min: int
    grade_max: int
    event_date: date
    registration_deadline: date
    city: str
    venue: str
    format: Literal["offline", "online", "hybrid"]
    terms: str
    capacity: int
    places_remaining: int
    registration_count: int
    status: Literal[
        "pending", "published", "rejected", "registration_closed", "completed"
    ]
    my_registration: RegistrationBrief | None
    created_at: datetime
