from typing import Literal, Self
from uuid import UUID

from pydantic import (
    Field,
    model_validator,
)

from app.schemas.shared.base import Input
from app.schemas.shared.types import Title


class PartnerDecision(Input):
    decision: Literal["accepted", "declined"]


class PartnershipCreate(Input):
    visibility: Literal["direct", "all_schools"]
    target_org_id: UUID | None = None
    title: Title
    description: str = Field(min_length=1, max_length=20000)

    @model_validator(mode="after")
    def valid_target(self) -> Self:
        if (self.visibility == "direct") != (self.target_org_id is not None):
            raise ValueError("Only direct requests require target_org_id")
        return self
