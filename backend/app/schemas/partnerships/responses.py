from datetime import datetime
from typing import Literal
from uuid import UUID

from app.schemas.organizations.responses import OrganizationOut
from app.schemas.shared.base import Output


class PartnershipResponseOut(Output):
    id: UUID
    request_id: UUID
    school: OrganizationOut | None
    organization: OrganizationOut
    status: Literal["pending", "accepted", "declined"]
    created_at: datetime
    decided_at: datetime | None


class PartnershipOut(Output):
    id: UUID
    sender: OrganizationOut
    target: OrganizationOut | None
    visibility: Literal["direct", "all_schools", "all_companies"]
    title: str
    description: str
    moderation_status: Literal["pending", "approved", "rejected"]
    direct_decision: Literal["accepted", "declined"] | None
    responses: list[PartnershipResponseOut]
    my_response: PartnershipResponseOut | None
    created_at: datetime
