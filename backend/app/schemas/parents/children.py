from datetime import datetime
from uuid import UUID

from app.schemas.parents.responses import ChildOut
from app.schemas.shared.base import Input, Output


class ChildrenOut(Output):
    items: list[ChildOut]
    active_child_id: UUID | None


class SuggestionCreate(Input):
    event_id: UUID


class SuggestionOut(Output):
    id: UUID
    student_user_id: UUID
    event_id: UUID
    title: str
    created_at: datetime
    status: str = "suggested"
