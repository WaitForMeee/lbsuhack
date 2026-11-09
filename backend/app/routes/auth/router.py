from app.routes.shared.router import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.demo import demo_preview
from app.core.errors import fail
from app.core.security import create_access_token, hash_password, verify_password
from app.models import StudentProfile, User
from app.routes.shared.dependencies import DB, Current
from app.schemas.auth.requests import Login, Register
from app.schemas.auth.access import OrganizationLogin
from app.services.organizations.credentials import token_hash
from app.schemas.auth.responses import SessionOut
from app.schemas.users.responses import UserOut
from app.services.organizations.access import school
from app.services.users.views import user_view

router = APIRouter(prefix="/auth", tags=["auth"])


def session_view(db, user):
    return dict(
        access_token=create_access_token(user.id, credential_version=user.credential_version if user.role in ("school", "company") else None),
        token_type="bearer",
        expires_in=28800,
        user=user_view(db, user),
    )


@router.post("/register", status_code=201, response_model=SessionOut)
def register(data: Register, db: DB):
    if data.role == "student":
        school(db, data.school_id)
    user = User(
        email=str(data.email).lower().strip(),
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
    )
    db.add(user)
    try:
        db.flush()
        if data.role == "student":
            db.add(
                StudentProfile(
                    user_id=user.id,
                    birth_date=data.birth_date,
                    school_id=data.school_id,
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        fail(409, "email_taken", "Email уже занят")
    return session_view(db, user)


@router.post("/login", response_model=SessionOut)
@demo_preview
def login(data: Login, db: DB):
    user = db.scalar(select(User).where(User.email == str(data.email).lower().strip()))
    if (
        not user
        or not user.is_active
        or user.role in ("school", "company")
        or not verify_password(data.password, user.password_hash)
        or (data.expected_role and user.role != data.expected_role)
    ):
        fail(401, "invalid_credentials", "Неверный email, пароль или роль")
    return session_view(db, user)


@router.post("/organization-login", response_model=SessionOut)
@demo_preview
def organization_login(data: OrganizationLogin, db: DB):
    user = db.scalar(select(User).where(User.organization_token_hash == token_hash(data.token)).with_for_update())
    if user is None or not user.is_active or user.role not in ("school", "company") or (data.expected_role and user.role != data.expected_role):
        fail(401, "invalid_credentials", "Неверный токен доступа или роль")
    return session_view(db, user)


@router.get("/me", response_model=UserOut)
def me(db: DB, user: Current):
    return user_view(db, user)
