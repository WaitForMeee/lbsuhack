from uuid import UUID

from pydantic import (
    ConfigDict,
)

from app.schemas.shared.base import Output
from app.schemas.shared.types import Role


class UserOut(Output):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "email": email + "@demo.by",
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "organization_id": "22222222-2222-4222-8222-222222222222"
                    if role in ("school", "company")
                    else None,
                    "profile_complete": True if role == "student" else None,
                }
                for email, first, last, role in [
                    ("alina", "Алина", "Коваль", "student"),
                    ("olga", "Ольга", "Коваль", "parent"),
                    ("school", "Елена", "Брик", "school"),
                    ("company", "Павел", "Мороз", "company"),
                    ("admin", "Админ", "TalentHub", "moderator"),
                ]
            ]
        },
    )
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: Role
    organization_id: UUID | None
    profile_complete: bool | None
