from uuid import UUID

from app.schemas.shared.base import Output


class InterestOut(Output):
    id: UUID
    name: str


class ReferenceOut(Output):
    grades: list[int]
    cities: list[str]
    formats: list[str]
    event_kinds: list[str]
    interests: list[InterestOut]
    direction_groups: dict[str, list[str]]
