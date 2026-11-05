from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.users.user import User
from app.scripts.seed_mock import MOCK_ORGANIZATIONS, MOCK_STUDENTS


def get_mock_emails() -> set[str]:
    representative_emails = {
        organization.representative_email for organization in MOCK_ORGANIZATIONS
    }
    student_emails = {student.email for student in MOCK_STUDENTS}
    return representative_emails | student_emails


def reset_mock_passwords() -> int:
    password = get_settings().mock_data_password
    if password is None or len(password) < 8:
        raise RuntimeError("Set MOCK_DATA_PASSWORD to at least 8 characters before resetting passwords")

    with SessionLocal.begin() as session:
        users = session.scalars(select(User).where(User.email.in_(get_mock_emails()))).all()
        for user in users:
            user.password_hash = hash_password(password)

    if not users:
        raise RuntimeError("No mock accounts were found. Run app.scripts.seed_mock first")

    print(f"Reset passwords for {len(users)} mock account(s).")
    return len(users)


if __name__ == "__main__":
    reset_mock_passwords()
