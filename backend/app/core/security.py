from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jwt import InvalidTokenError

from app.core.config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(
    user_id: UUID, *, expires_delta: timedelta | None = None,
    credential_version: int | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + (expires_delta or timedelta(hours=8))
    claims = {"sub": str(user_id), "iat": now, "exp": expires_at, "purpose": "access"}
    if credential_version is not None:
        claims["credential_version"] = credential_version
    return jwt.encode(
        claims,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_claims(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
        UUID(payload["sub"])
        if payload.get("purpose", "access") != "access":
            raise ValueError("Invalid token purpose")
        return payload
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid access token") from exc


def decode_access_token(token: str) -> UUID:
    return UUID(decode_access_claims(token)["sub"])
