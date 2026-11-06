from datetime import date
from uuid import UUID

from app.schemas.organizations.responses import OrganizationOut
from app.schemas.shared.base import Output
from app.schemas.shared.types import Kind


class EventBrief(Output):
    id: UUID
    title: str
    event_date: date
    city: str
    kind: Kind
    format: str
    status: str
    organizer: OrganizationOut
