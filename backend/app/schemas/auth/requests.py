from datetime import date
from typing import Literal, Self
from uuid import UUID

from pydantic import (
    EmailStr,
    Field,
    model_validator,
)

from app.schemas.shared.base import Input
from app.schemas.shared.types import Name, Password, Role


class Login(Input):
    email: EmailStr
    password: Password
    expected_role: Role | None = None


class Register(Input):
    role: Literal["student", "parent"]
    first_name: Name
    last_name: Name
    email: EmailStr
    password: Password = Field(min_length=8, max_length=128)
    birth_date: date | None = None
    school_id: UUID | None = None

    @model_validator(mode="after")
    def valid_student(self) -> Self:
        if self.role == "student" and (
            self.birth_date is None or self.school_id is None
        ):
            raise ValueError("Student requires birth_date and school_id")
        return self
