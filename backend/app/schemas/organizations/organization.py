from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.organizations.organization import OrganizationType


class PrestigeEntryRead(BaseModel):
    id: UUID
    points: int
    reason: str
    created_at: datetime


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    type: OrganizationType
    description: str
    region: str
    contact_email: str | None
    website_url: str | None
    directions: str
    prestige_score: int
    prestige_history: list[PrestigeEntryRead]
    published_event_count: int


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=3000)
    region: str = Field(min_length=2, max_length=120)
    contact_email: EmailStr | None = None
    website_url: str | None = Field(default=None, max_length=500)
    directions: str = Field(default="", max_length=1000)
