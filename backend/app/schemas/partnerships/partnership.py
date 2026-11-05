from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.partnerships.partnership import (
    OpportunityDirection,
    OpportunityStatus,
    PartnershipStatus,
    ResponseStatus,
)


class OrganizationBrief(BaseModel):
    id: UUID
    name: str
    type: str
    prestige_score: int = 0


class OpportunityCreate(BaseModel):
    direction: OpportunityDirection
    target_organization_id: UUID | None = None
    title: str = Field(min_length=3, max_length=220)
    description: str = Field(min_length=20, max_length=5000)
    topic: str = Field(min_length=2, max_length=180)
    format: str = Field(min_length=2, max_length=120)
    target_audience: str = Field(min_length=2, max_length=300)
    conditions: str = Field(default="", max_length=3000)
    desired_start: date | None = None
    desired_end: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "OpportunityCreate":
        if self.desired_start and self.desired_end and self.desired_end < self.desired_start:
            raise ValueError("Конечная дата должна быть позже начальной")
        return self


class ResponseCreate(BaseModel):
    message: str = Field(min_length=3, max_length=3000)


class ResponseUpdate(BaseModel):
    status: ResponseStatus


class ResponseRead(BaseModel):
    id: UUID
    responder: OrganizationBrief
    message: str
    status: ResponseStatus
    created_at: datetime


class OpportunityRead(BaseModel):
    id: UUID
    creator: OrganizationBrief
    target: OrganizationBrief | None
    direction: OpportunityDirection
    title: str
    description: str
    topic: str
    format: str
    target_audience: str
    conditions: str
    desired_start: date | None
    desired_end: date | None
    status: OpportunityStatus
    created_at: datetime
    responses: list[ResponseRead]


class PartnershipRead(BaseModel):
    id: UUID
    title: str
    organization_a: OrganizationBrief
    organization_b: OrganizationBrief
    organization_a_confirmed: bool
    organization_b_confirmed: bool
    status: PartnershipStatus
    completed_at: datetime | None
    created_at: datetime
