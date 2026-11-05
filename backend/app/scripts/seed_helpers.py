from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.organizations.organization import Organization, OrganizationType
from app.models.profiles.student_profile import StudentProfile
from app.models.users.user import User, UserRole


@dataclass(frozen=True)
class SeedUser:
    email: str
    full_name: str
    role: UserRole


def get_or_create_organization(
    session: Session,
    name: str,
    organization_type: OrganizationType,
    description: str,
) -> tuple[Organization, bool]:
    organization = session.scalar(select(Organization).where(Organization.name == name))
    if organization is not None:
        return organization, False

    organization = Organization(name=name, type=organization_type, description=description)
    session.add(organization)
    session.flush()
    return organization, True


def create_user_if_missing(
    session: Session,
    seed_user: SeedUser,
    password: str,
    organization: Organization | None = None,
) -> bool:
    existing = session.scalar(select(User).where(User.email == seed_user.email))
    if existing is not None:
        return False

    user = User(
            email=seed_user.email,
            full_name=seed_user.full_name,
            role=seed_user.role,
            password_hash=hash_password(password),
            organization=organization,
        )
    if seed_user.role == UserRole.STUDENT:
        user.student_profile = StudentProfile()
    session.add(user)
    return True
