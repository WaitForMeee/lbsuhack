from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.errors import fail
from app.models import Event, EventRegistration
from app.routes.shared.dependencies import DB, OptionalUser, Organizer, Student
from app.schemas.events.requests import EventCreate
from app.schemas.events.responses import EventOut
from app.schemas.shared.base import Items
from app.schemas.shared.types import Kind
from app.services.events.recommendations import recommendation_cards
from app.services.events.service import transition
from app.services.events.views import event_view
from app.services.interests.service import resolve_interests
from app.services.shared.repository import get
from app.services.shared.text import normalize
from app.services.shared.time import today

router = APIRouter(tags=["events"])


@router.get("/events", response_model=Items[EventOut])
def catalog(
    db: DB,
    user: OptionalUser,
    q: str = "",
    kind: Kind | None = None,
    interest: Annotated[list[str] | None, Query()] = None,
    upcoming: bool = False,
    application_status: Literal[
        "none",
        "submitted",
        "under_review",
        "waitlisted",
        "approved",
        "rejected",
        "cancelled",
    ]
    | None = None,
):
    if application_status and (user is None or user.role != "student"):
        fail(
            401 if user is None else 403,
            "personal_filter_unavailable",
            "Фильтр заявок доступен ученику",
        )
    events = list(
        db.scalars(
            select(Event)
            .where(Event.status == "published")
            .order_by(Event.event_date, Event.id)
        )
    )
    statuses = (
        {
            r.event_id: r.status
            for r in db.scalars(
                select(EventRegistration).where(
                    EventRegistration.student_user_id == user.id
                )
            )
        }
        if user and user.role == "student"
        else {}
    )
    wanted = {normalize(i) for i in interest or []}
    result = []
    for e in events:
        if kind and e.kind != kind or upcoming and e.event_date < today():
            continue
        if wanted and not wanted.intersection(i.normalized_name for i in e.interests):
            continue
        if (
            application_status == "none"
            and e.id in statuses
            or application_status
            and application_status != "none"
            and statuses.get(e.id) != application_status
        ):
            continue
        card = event_view(db, e, user)
        search = " ".join(
            [
                e.title,
                e.description,
                card["organizer"]["name"],
                e.city,
                e.venue,
                e.terms,
                e.project_kind or "",
                *(i.name for i in e.interests),
            ]
        )
        if q and normalize(q) not in normalize(search):
            continue
        result.append(card)
    return dict(items=result)


@router.get("/recommendations", response_model=Items[EventOut])
def recommendations(
    db: DB, user: Student, interest: Annotated[list[str] | None, Query()] = None
):
    return recommendation_cards(db, user, interest)


@router.post("/events", status_code=201, response_model=EventOut)
def create(data: EventCreate, db: DB, user: Organizer):
    values = data.model_dump(exclude={"interests"})
    e = Event(
        **values,
        organizer_id=user.organization_id,
        interests=resolve_interests(db, data.interests),
    )
    db.add(e)
    db.commit()
    return event_view(db, e, user)


@router.get("/events/{identity}", response_model=EventOut)
def detail(identity: UUID, db: DB, user: OptionalUser):
    e = get(db, Event, identity)
    if e.status != "published":
        own = user and (
            user.role == "moderator" or user.organization_id == e.organizer_id
        )
        history = (
            user
            and user.role == "student"
            and db.scalar(
                select(EventRegistration.id).where(
                    EventRegistration.event_id == e.id,
                    EventRegistration.student_user_id == user.id,
                )
            )
        )
        if not own and not history:
            fail(404, "not_found", "Мероприятие не найдено")
    return event_view(db, e, user)


@router.post("/events/{identity}/close-registration", response_model=EventOut)
def close(identity: UUID, db: DB, user: Organizer):
    return event_view(db, transition(db, identity, user, "registration_closed"), user)


@router.post("/events/{identity}/open-registration", response_model=EventOut)
def reopen(identity: UUID, db: DB, user: Organizer):
    return event_view(db, transition(db, identity, user, "published"), user)


@router.post("/events/{identity}/complete", response_model=EventOut)
def complete(identity: UUID, db: DB, user: Organizer):
    return event_view(db, transition(db, identity, user, "completed"), user)
