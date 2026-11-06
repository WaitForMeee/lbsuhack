from datetime import date
from typing import Literal, Self

from pydantic import (
    Field,
    model_validator,
)

from app.schemas.shared.base import Input
from app.schemas.shared.types import Kind, Name, Title


class EventCreate(Input):
    title: Title
    description: str = Field(min_length=1, max_length=20000)
    kind: Kind
    project_kind: Name | None = None
    interests: list[Name] = Field(max_length=50)
    grade_min: int = Field(strict=True, ge=7, le=11)
    grade_max: int = Field(strict=True, ge=7, le=11)
    event_date: date
    registration_deadline: date
    city: Name
    venue: Title
    format: Literal["offline", "online", "hybrid"]
    terms: str = Field(max_length=20000)
    capacity: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def valid_event(self) -> Self:
        if (
            self.grade_min > self.grade_max
            or self.registration_deadline > self.event_date
        ):
            raise ValueError("Invalid grade range or deadline")
        if self.kind == "olympiad" and self.project_kind is not None:
            raise ValueError("project_kind is only applicable to projects")
        return self
