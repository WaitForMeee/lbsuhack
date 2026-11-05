from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.achievements.achievement import Achievement
from app.models.events.event import Event
from app.models.organizations.organization import Organization
from app.models.profiles.student_profile import StudentProfile
from app.models.registrations.registration import EventRegistration, RegistrationStatus
from app.models.users.user import User
from app.scripts.seed_mock import MOCK_ORGANIZATIONS, MOCK_STUDENTS, PRIMARY_DEMO_STUDENT, seed_mock_data


def test_mock_seed_is_repeatable_and_preserves_passwords():
    assert seed_mock_data("first-mock-password") == (
        len(MOCK_ORGANIZATIONS),
        len(MOCK_ORGANIZATIONS) + len(MOCK_STUDENTS),
    )

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == MOCK_STUDENTS[0].email))
        assert user is not None
        original_password_hash = user.password_hash
        user_count = session.scalar(select(func.count()).select_from(User))
        organization_count = session.scalar(select(func.count()).select_from(Organization))
        assert session.scalar(select(func.count()).select_from(Event)) == 20
        assert session.scalar(select(func.count(func.distinct(Event.image_url))).select_from(Event)) == 20

        for email in (PRIMARY_DEMO_STUDENT.email, MOCK_STUDENTS[0].email):
            featured = session.scalar(
                select(User)
                .options(selectinload(User.student_profile).selectinload(StudentProfile.interests))
                .where(User.email == email)
            )
            assert featured is not None and featured.student_profile is not None
            assert len(featured.student_profile.interests) >= 3
            registrations = list(
                session.scalars(
                    select(EventRegistration).where(EventRegistration.student_id == featured.id)
                ).all()
            )
            assert len(registrations) == 5
            assert {item.status for item in registrations} == {
                RegistrationStatus.PENDING,
                RegistrationStatus.APPROVED,
                RegistrationStatus.REJECTED,
                RegistrationStatus.CANCELLED,
                RegistrationStatus.ATTENDED,
            }
            assert session.scalar(
                select(func.count()).select_from(Achievement).where(Achievement.student_id == featured.id)
            ) == 1

        primary = session.scalar(select(User).where(User.email == PRIMARY_DEMO_STUDENT.email))
        primary.full_name = "Пользовательское имя"
        custom_event = session.scalar(select(Event).where(Event.slug == "python-lab"))
        custom_event.description = "Пользователь изменил описание события и сидер не должен его заменять."
        session.commit()

    assert seed_mock_data("different-mock-password") == (0, 0)

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == MOCK_STUDENTS[0].email))
        assert user is not None
        assert user.password_hash == original_password_hash
        assert session.scalar(select(func.count()).select_from(User)) == user_count
        assert session.scalar(select(func.count()).select_from(Organization)) == organization_count
        primary = session.scalar(select(User).where(User.email == PRIMARY_DEMO_STUDENT.email))
        assert primary.full_name == "Пользовательское имя"
        custom_event = session.scalar(select(Event).where(Event.slug == "python-lab"))
        assert custom_event.description == "Пользователь изменил описание события и сидер не должен его заменять."
