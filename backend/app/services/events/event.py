import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.categories.category import Category
from app.models.events.event import Event
from app.models.registrations.registration import EventRegistration, RegistrationStatus
from app.schemas.events.event import EventRead, OrganizerRead
from app.schemas.profiles.profile import CategoryRead


def make_event_slug() -> str:
    return f"event-{uuid.uuid4().hex[:12]}"


def load_categories(session: Session, category_ids: list[uuid.UUID]) -> list[Category]:
    categories = list(session.scalars(select(Category).where(Category.id.in_(category_ids))).all())
    if len({category.id for category in categories}) != len(set(category_ids)):
        raise ValueError("Одна или несколько категорий не найдены")
    return categories


def event_to_read(
    session: Session,
    event: Event,
    current_user_id: uuid.UUID | None = None,
    registration_count: int | None = None,
    my_status: RegistrationStatus | None = None,
    status_preloaded: bool = False,
) -> EventRead:
    if registration_count is None:
        registration_count = session.scalar(
            select(func.count()).select_from(EventRegistration).where(EventRegistration.event_id == event.id)
        ) or 0
    if current_user_id is not None and not status_preloaded:
        registration = session.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event.id,
                EventRegistration.student_id == current_user_id,
            )
        )
        my_status = registration.status if registration else None
    return EventRead(
        id=event.id,
        slug=event.slug,
        title=event.title,
        summary=event.summary,
        description=event.description,
        image_url=event.image_url,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        registration_deadline=event.registration_deadline,
        format=event.format,
        region=event.region,
        venue=event.venue,
        address=event.address,
        meeting_url=event.meeting_url,
        target_audience=event.target_audience,
        min_grade=event.min_grade,
        max_grade=event.max_grade,
        participation_terms=event.participation_terms,
        capacity=event.capacity,
        requires_approval=event.requires_approval,
        status=event.status,
        organizer=OrganizerRead(id=event.organizer.id, name=event.organizer.name, type=event.organizer.type.value),
        categories=[CategoryRead(id=item.id, slug=item.slug, name=item.name) for item in event.categories],
        registration_count=registration_count,
        my_registration_status=my_status,
    )


def events_to_read(
    session: Session,
    events: list[Event],
    current_user_id: uuid.UUID | None = None,
) -> list[EventRead]:
    """Serialize an event collection with a constant number of SQL queries."""
    if not events:
        return []

    event_ids = [event.id for event in events]
    counts = dict(
        session.execute(
            select(EventRegistration.event_id, func.count())
            .where(EventRegistration.event_id.in_(event_ids))
            .group_by(EventRegistration.event_id)
        ).all()
    )
    statuses: dict[uuid.UUID, RegistrationStatus] = {}
    if current_user_id is not None:
        statuses = dict(
            session.execute(
                select(EventRegistration.event_id, EventRegistration.status).where(
                    EventRegistration.event_id.in_(event_ids),
                    EventRegistration.student_id == current_user_id,
                )
            ).all()
        )

    return [
        event_to_read(
            session,
            event,
            current_user_id,
            registration_count=counts.get(event.id, 0),
            my_status=statuses.get(event.id),
            status_preloaded=True,
        )
        for event in events
    ]


def registration_is_open(event: Event) -> bool:
    now = datetime.now(UTC)
    if event.registration_deadline is not None and event.registration_deadline.tzinfo is None:
        now = now.replace(tzinfo=None)
    return event.registration_deadline is None or event.registration_deadline >= now
