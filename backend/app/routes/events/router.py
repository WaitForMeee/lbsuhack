from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db_session
from app.models.events.event import Event, EventFormat, EventStatus
from app.models.users.user import User
from app.routes.auth.dependencies import OptionalCurrentUser, OrganizationUser, StudentUser
from app.schemas.events.event import EventCreate, EventList, EventRead, EventUpdate
from app.services.events.event import event_to_read, events_to_read, load_categories, make_event_slug

router = APIRouter(tags=["events"])


def event_query():
    return select(Event).options(joinedload(Event.organizer), selectinload(Event.categories))


@router.get("/events", response_model=EventList)
def list_events(session: Annotated[Session, Depends(get_db_session)], user: OptionalCurrentUser, search: str | None = None, category: str | None = None, format: EventFormat | None = None, region: str | None = None, organizer_id: UUID | None = None, mine: bool = False, include_past: bool = False) -> EventList:
    query = event_query()
    if mine:
        if user is None or user.organization_id is None: raise HTTPException(403, "Доступно только представителю организации")
        query = query.where(Event.organizer_id == user.organization_id)
    else:
        query = query.where(Event.status == EventStatus.PUBLISHED)
    if not include_past: query = query.where(Event.ends_at >= datetime.now(UTC))
    if search:
        pattern = f"%{search.strip()}%"; query = query.where(or_(Event.title.ilike(pattern), Event.summary.ilike(pattern), Event.description.ilike(pattern)))
    if category: query = query.where(Event.categories.any(slug=category))
    if format: query = query.where(Event.format == format)
    if region: query = query.where(Event.region == region)
    if organizer_id: query = query.where(Event.organizer_id == organizer_id)
    events = list(session.scalars(query.order_by(Event.starts_at)).unique().all())
    return EventList(items=events_to_read(session, events, user.id if user else None), total=len(events))


@router.get("/events/{identifier}", response_model=EventRead)
def get_event(identifier: str, session: Annotated[Session, Depends(get_db_session)], user: OptionalCurrentUser) -> EventRead:
    try:
        event_id = UUID(identifier)
    except ValueError:
        event_id = None
    event = session.scalar(event_query().where(Event.id == event_id if event_id else Event.slug == identifier))
    if event is None: raise HTTPException(404, "Событие не найдено")
    if event.status != EventStatus.PUBLISHED and (user is None or user.organization_id != event.organizer_id): raise HTTPException(404, "Событие не найдено")
    return event_to_read(session, event, user.id if user else None)


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(payload: EventCreate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> EventRead:
    event = Event(**payload.model_dump(exclude={"category_ids"}), slug=make_event_slug(), organizer_id=user.organization_id, categories=load_categories(session, payload.category_ids))
    session.add(event); session.commit(); session.refresh(event)
    return event_to_read(session, event, user.id)


@router.put("/events/{event_id}", response_model=EventRead)
def update_event(event_id: UUID, payload: EventUpdate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> EventRead:
    event = session.scalar(event_query().where(Event.id == event_id))
    if event is None: raise HTTPException(404, "Событие не найдено")
    if event.organizer_id != user.organization_id: raise HTTPException(403, "Можно редактировать только свои события")
    if event.status == EventStatus.CANCELLED: raise HTTPException(409, "Отменённое событие нельзя редактировать")
    for key, value in payload.model_dump(exclude={"category_ids"}).items(): setattr(event, key, value)
    event.categories = load_categories(session, payload.category_ids)
    session.commit(); return event_to_read(session, event, user.id)


def change_status(event_id: UUID, target: EventStatus, user: User, session: Session) -> EventRead:
    event = session.scalar(event_query().where(Event.id == event_id))
    if event is None: raise HTTPException(404, "Событие не найдено")
    if event.organizer_id != user.organization_id: raise HTTPException(403, "Можно управлять только своими событиями")
    if event.status == EventStatus.CANCELLED: raise HTTPException(409, "Отменённое событие нельзя изменить")
    event.status = target; session.commit(); return event_to_read(session, event, user.id)


@router.post("/events/{event_id}/publish", response_model=EventRead)
def publish(event_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]): return change_status(event_id, EventStatus.PUBLISHED, user, session)

@router.post("/events/{event_id}/unpublish", response_model=EventRead)
def unpublish(event_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]): return change_status(event_id, EventStatus.DRAFT, user, session)

@router.post("/events/{event_id}/cancel", response_model=EventRead)
def cancel(event_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]): return change_status(event_id, EventStatus.CANCELLED, user, session)


@router.get("/recommendations", response_model=EventList)
def recommendations(user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> EventList:
    from app.models.profiles.student_profile import StudentProfile
    profile = session.scalar(select(StudentProfile).options(selectinload(StudentProfile.interests)).where(StudentProfile.user_id == user.id))
    query = event_query().where(Event.status == EventStatus.PUBLISHED, Event.ends_at >= datetime.now(UTC))
    events = list(session.scalars(query.order_by(Event.starts_at)).unique().all())
    interests = {item.id for item in (profile.interests if profile else [])}
    events.sort(key=lambda item: (-len(interests & {cat.id for cat in item.categories}), item.starts_at))
    return EventList(items=events_to_read(session, events, user.id), total=len(events))
