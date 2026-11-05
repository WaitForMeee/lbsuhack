from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.organizations.organization import Organization, OrganizationType
from app.models.users.user import UserRole
from app.scripts.seed_helpers import SeedUser, create_user_if_missing, get_or_create_organization


def seed_demo() -> None:
    settings = get_settings()
    passwords = (
        settings.demo_student_password,
        settings.demo_institution_password,
        settings.demo_company_password,
    )
    if any(password is None or len(password) < 8 for password in passwords):
        raise RuntimeError("Set all DEMO_*_PASSWORD values to at least 8 characters before seeding")

    with SessionLocal.begin() as session:
        lyceum, _ = get_or_create_organization(
            session,
            "Лицей БГУ",
            OrganizationType.INSTITUTION,
            "Образовательное учреждение для талантливых учащихся.",
        )
        company, _ = get_or_create_organization(
            session,
            "ТехноСтарт",
            OrganizationType.COMPANY,
            "Демонстрационная технологическая компания.",
        )
        demo_users = (
            (SeedUser("student@talenthub.by", "Анна Коваль", UserRole.STUDENT), passwords[0], None),
            (
                SeedUser(
                    "lyceum@talenthub.by",
                    "Мария Орлова",
                    UserRole.INSTITUTION_REPRESENTATIVE,
                ),
                passwords[1],
                lyceum,
            ),
            (
                SeedUser(
                    "company@talenthub.by",
                    "Алексей Миронов",
                    UserRole.ORGANIZATION_REPRESENTATIVE,
                ),
                passwords[2],
                company,
            ),
        )
        created = sum(
            create_user_if_missing(session, user, password, organization)
            for user, password, organization in demo_users
        )

    print(f"Demo seed complete. Created {created} user(s); existing users were preserved.")


if __name__ == "__main__":
    seed_demo()
