from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.achievements.achievement import Achievement
from app.models.registrations.registration import EventRegistration, RegistrationStatus
from app.schemas.registrations.registration import RegistrationRead

ALLOWED_TRANSITIONS = {
    RegistrationStatus.PENDING: {RegistrationStatus.APPROVED, RegistrationStatus.REJECTED, RegistrationStatus.CANCELLED},
    RegistrationStatus.APPROVED: {RegistrationStatus.CANCELLED, RegistrationStatus.ATTENDED},
    RegistrationStatus.REJECTED: set(),
    RegistrationStatus.CANCELLED: set(),
    RegistrationStatus.ATTENDED: set(),
}


def transition_registration(
    session: Session,
    registration: EventRegistration,
    new_status: RegistrationStatus,
) -> None:
    if new_status not in ALLOWED_TRANSITIONS[registration.status]:
        raise ValueError(f"Нельзя изменить статус {registration.status.value} на {new_status.value}")
    registration.status = new_status
    if new_status == RegistrationStatus.ATTENDED and registration.achievement is None:
        registration.achievement = Achievement(
            student_id=registration.student_id,
            title=registration.event.title,
            description=f"Подтверждённое участие в событии «{registration.event.title}».",
            issued_at=datetime.now(UTC),
        )
    session.flush()


def registration_to_read(registration: EventRegistration) -> RegistrationRead:
    return RegistrationRead(
        id=registration.id,
        event_id=registration.event.id,
        event_slug=registration.event.slug,
        event_title=registration.event.title,
        event_image_url=registration.event.image_url,
        event_starts_at=registration.event.starts_at,
        organizer_name=registration.event.organizer.name,
        student_id=registration.student.id,
        student_name=registration.student.full_name,
        student_email=registration.student.email,
        status=registration.status,
        created_at=registration.created_at,
    )
