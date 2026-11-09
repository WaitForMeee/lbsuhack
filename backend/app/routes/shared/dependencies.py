from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.demo import preview_only, DemoRestricted
from app.core.errors import fail
from app.core.security import decode_access_claims
from uuid import UUID
from app.db.session import get_db_session
from app.models import Organization, User

DB = Annotated[Session, Depends(get_db_session)]
bearer = HTTPBearer(auto_error=False)


def optional_user(
    request: Request,
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if credentials is None:
        if request.headers.get("Authorization"):
            fail(401, "invalid_token", "Ожидается Authorization: Bearer <token>")
        return None
    try:
        claims = decode_access_claims(credentials.credentials)
        identity = UUID(claims["sub"])
    except ValueError:
        fail(401, "invalid_token", "Недействительный или истёкший токен")
    user = db.get(User, identity)
    if user is None or not user.is_active:
        fail(401, "invalid_token", "Недействительный токен")
    if user.role in ("school", "company") and claims.get("credential_version") != user.credential_version:
        fail(401, "invalid_token", "Доступ перевыпущен. Войдите с новым токеном")
    request.state.demo_read_only = preview_only(user)
    return user


def current_user(user: Annotated[User | None, Depends(optional_user)]):
    if user is None:
        fail(401, "authentication_required", "Требуется вход")
    return user


def roles(*allowed):
    def dependency(db: DB, user: Annotated[User, Depends(current_user)]):
        if user.role not in allowed:
            fail(403, "forbidden", "Операция недоступна этой роли")
        if user.role in ("school", "company"):
            org = db.get(Organization, user.organization_id)
            if org is None or (user.role == "school") != (org.kind == "school"):
                fail(403, "invalid_organization", "Неверная организация представителя")
        return user

    dependency.allowed_roles = allowed
    return dependency


Student = Annotated[User, Depends(roles("student"))]
Parent = Annotated[User, Depends(roles("parent"))]
Organizer = Annotated[User, Depends(roles("school", "company"))]
School = Annotated[User, Depends(roles("school"))]
Moderator = Annotated[User, Depends(roles("moderator"))]
Current = Annotated[User, Depends(current_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]


def enforce_demo_write_policy(request: Request, user: OptionalUser):
    if user is None or not preview_only(user) or request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    # Preserve role errors before reporting a demo limitation on known routes.
    def role_constraints(dependant):
        allowed = getattr(dependant.call, "allowed_roles", None)
        if allowed is not None:
            yield allowed
        for child in dependant.dependencies:
            yield from role_constraints(child)
    route = request.scope.get("route")
    if route is not None and hasattr(route, "dependant"):
        if any(user.role not in allowed for allowed in role_constraints(route.dependant)):
            return
    if "/auth/" in request.url.path:
        return
    if not getattr(request.scope.get("endpoint"), "demo_preview", False):
        raise DemoRestricted()
