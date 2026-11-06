from typing import Literal

from app.schemas.shared.base import Input


class RegistrationDecision(Input):
    decision: Literal["approved", "rejected"]
