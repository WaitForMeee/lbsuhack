from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.routes.auth.dependencies import CurrentUser
from app.schemas.auth.auth import AuthenticatedUser, LoginRequest, RegisterRequest
from app.services.auth.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthenticatedUser)
def login(
    credentials: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser:
    user = authenticate_user(session, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверная почта или пароль")

    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user.id),
        max_age=settings.jwt_expiration_hours * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return AuthenticatedUser.model_validate(user)


@router.post("/register", response_model=AuthenticatedUser, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser:
    try:
        user = register_user(session, payload)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user.id),
        max_age=settings.jwt_expiration_hours * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return AuthenticatedUser.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        settings.auth_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.get("/me", response_model=AuthenticatedUser)
def get_me(user: CurrentUser) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(user)
