from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)

T = TypeVar("T")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def utc_timestamps(cls, value):
        # SQLite drops timezone metadata; persisted timestamps still represent UTC.
        if isinstance(value, datetime):
            return (
                value.replace(tzinfo=UTC)
                if value.tzinfo is None
                else value.astimezone(UTC)
            )
        return value


class Items(Output, Generic[T]):
    items: list[T]


class QueueSection(Items[T], Generic[T]):
    decided_count: int
