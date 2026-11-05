from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.events.event import EventFormat, EventStatus
from app.models.registrations.registration import RegistrationStatus
from app.schemas.profiles.profile import CategoryRead


class OrganizerRead(BaseModel):
    id: UUID
    name: str
    type: str


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=220)
    summary: str = Field(min_length=10, max_length=400)
    description: str = Field(min_length=20, max_length=10000)
    image_url: str | None = Field(default=None, max_length=1000)
    starts_at: datetime
    ends_at: datetime
    registration_deadline: datetime | None = None
    format: EventFormat
    region: str = Field(min_length=2, max_length=120)
    venue: str | None = Field(default=None, max_length=220)
    address: str | None = Field(default=None, max_length=500)
    meeting_url: str | None = Field(default=None, max_length=1000)
    target_audience: str = Field(min_length=3, max_length=500)
    min_grade: int = Field(ge=1, le=11)
    max_grade: int = Field(ge=1, le=11)
    participation_terms: str = Field(default="", max_length=3000)
    capacity: int | None = Field(default=None, ge=1, le=100000)
    requires_approval: bool = False
    category_ids: list[UUID] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_dates_and_grades(self) -> "EventBase":
        if self.ends_at <= self.starts_at:
            raise ValueError("Время завершения должно быть позже начала")
        if self.registration_deadline and self.registration_deadline > self.starts_at:
            raise ValueError("Регистрация должна завершиться до начала")
        if self.min_grade > self.max_grade:
            raise ValueError("Минимальный класс не может быть больше максимального")
        if self.format == EventFormat.ONLINE and not self.meeting_url:
            raise ValueError("Для онлайн-события укажите ссылку")
        return self


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventRead(BaseModel):
    id: UUID
    slug: str
    title: str
    summary: str
    description: str
    image_url: str | None
    starts_at: datetime
    ends_at: datetime
    registration_deadline: datetime | None
    format: EventFormat
    region: str
    venue: str | None
    address: str | None
    meeting_url: str | None
    target_audience: str
    min_grade: int
    max_grade: int
    participation_terms: str
    capacity: int | None
    requires_approval: bool
    status: EventStatus
    organizer: OrganizerRead
    categories: list[CategoryRead]
    registration_count: int = 0
    my_registration_status: RegistrationStatus | None = None


class EventList(BaseModel):
    items: list[EventRead]
    total: int
