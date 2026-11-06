from typing import Literal

from app.schemas.shared.base import Output
from app.schemas.users.responses import UserOut


class SessionOut(Output):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 28800
    user: UserOut
