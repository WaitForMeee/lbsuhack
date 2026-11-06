from typing import Annotated, Literal

from pydantic import (
    Field,
    StringConstraints,
)

Role = Literal["student", "parent", "school", "company", "moderator"]


Kind = Literal["olympiad", "project"]


RegistrationStatus = Literal[
    "submitted", "under_review", "waitlisted", "approved", "rejected", "cancelled"
]


Name = Annotated[str, Field(min_length=1, max_length=100)]


Title = Annotated[str, Field(min_length=1, max_length=250)]


Password = Annotated[str, StringConstraints(strip_whitespace=False)]
