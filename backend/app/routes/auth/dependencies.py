from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.users.user import User
from app.models.users.user import UserRole


def get_current_user(
    session: Annotated[Session, Depends(get_db_session)],
    session_cookie: Annotated[str | None, Cookie(alias=get_settings().auth_cookie_name)] = None,
) -> User:
    if session_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход")
    try:
        user_id = decode_access_token(session_cookie)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительная сессия") from exc

    user = session.scalar(
        select(User).options(joinedload(User.organization)).where(User.id == user_id)
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительная сессия")
    return user


def get_optional_user(
    session: Annotated[Session, Depends(get_db_session)],
    session_cookie: Annotated[str | None, Cookie(alias=get_settings().auth_cookie_name)] = None,
) -> User | None:
    if session_cookie is None:
        return None
    try:
        user_id = decode_access_token(session_cookie)
    except ValueError:
        return None
    return session.scalar(
        select(User).options(joinedload(User.organization)).where(User.id == user_id, User.is_active.is_(True))
    )


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user

    return dependency


StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
OrganizationUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.INSTITUTION_REPRESENTATIVE,
            UserRole.ORGANIZATION_REPRESENTATIVE,
        )
    ),
]
