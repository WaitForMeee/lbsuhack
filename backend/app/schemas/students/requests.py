from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    Field,
    model_validator,
)

from app.schemas.shared.base import Input
from app.schemas.shared.types import Name


class ProfileUpdate(Input):
    school_id: UUID | None = None
    grade: Annotated[int, Field(strict=True, ge=7, le=11)] | None = None
    city: Name | None = None
    interests: list[Name] | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def no_null(self) -> Self:
        if any(getattr(self, k) is None for k in self.model_fields_set):
            raise ValueError(
                "Explicit null is not supported; use [] to clear interests"
            )
        return self
