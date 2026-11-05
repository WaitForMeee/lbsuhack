from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryRead(BaseModel):
    id: UUID
    slug: str
    name: str


class StudentProfileRead(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    grade: int
    region: str
    bio: str
    interests: list[CategoryRead]


class StudentProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    grade: int = Field(ge=1, le=11)
    region: str = Field(min_length=2, max_length=120)
    bio: str = Field(default="", max_length=2000)


class InterestsUpdate(BaseModel):
    category_ids: list[UUID] = Field(max_length=20)


class AchievementRead(BaseModel):
    id: UUID
    title: str
    description: str
    issued_at: datetime
    event_id: UUID
    event_slug: str
    event_image_url: str | None
    organizer_name: str
