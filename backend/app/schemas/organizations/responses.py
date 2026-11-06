from typing import Literal
from uuid import UUID

from app.schemas.shared.base import Output
from app.schemas.users.responses import UserOut


class OrganizationOut(Output):
    id: UUID
    kind: Literal["school", "company", "academy"]
    name: str
    city: str
    description: str
    directions: list[str]


class SchoolOut(Output):
    id: UUID
    name: str


class Counters(Output):
    students: int
    events: int
    initiatives: int
    published: int
    pending_moderation: int
    incoming_requests: int
    total_requests: int
    agreed_initiatives: int
    registrations: int


class DashboardOut(Output):
    organization: OrganizationOut
    representative: UserOut
    counters: Counters
