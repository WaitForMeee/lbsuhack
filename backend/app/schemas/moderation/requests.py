from typing import Literal

from app.schemas.shared.base import Input


class ModerationDecision(Input):
    decision: Literal["approve", "reject"]
