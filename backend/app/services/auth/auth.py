from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.organizations.organization import Organization
from app.models.profiles.student_profile import StudentProfile
from app.core.security import verify_password
from app.models.users.user import User
from app.models.users.user import UserRole
from app.schemas.auth.auth import RegisterRequest


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = session.scalar(
        select(User).options(joinedload(User.organization)).where(User.email == normalized_email)
    )
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def register_user(session: Session, payload: RegisterRequest) -> User:
    email = payload.email.strip().lower()
    if session.scalar(select(User.id).where(User.email == email)) is not None:
        raise ValueError("Пользователь с такой почтой уже существует")

    organization = None
    if payload.role != UserRole.STUDENT:
        if session.scalar(select(Organization.id).where(Organization.name == payload.organization_name)):
            raise ValueError("Организация с таким названием уже существует")
        organization = Organization(
            name=payload.organization_name or "",
            type=payload.organization_type,
            description=payload.organization_description,
            region=payload.region,
            contact_email=email,
        )
        session.add(organization)

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization=organization,
    )
    if payload.role == UserRole.STUDENT:
        user.student_profile = StudentProfile(grade=payload.grade or 10, region=payload.region)
    session.add(user)
    session.flush()
    session.refresh(user)
    return user
