from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db_session
from app.models.events.event import Event, EventStatus
from app.models.registrations.registration import EventRegistration, RegistrationStatus
from app.routes.auth.dependencies import OrganizationUser, StudentUser
from app.schemas.registrations.registration import RegistrationRead, RegistrationStatusUpdate
from app.services.events.event import registration_is_open
from app.services.registrations.registration import registration_to_read, transition_registration

router = APIRouter(tags=["registrations"])


def registration_query():
    return select(EventRegistration).options(
        joinedload(EventRegistration.event).joinedload(Event.organizer),
        joinedload(EventRegistration.student),
        joinedload(EventRegistration.achievement),
    )


@router.post("/events/{event_id}/registrations", response_model=RegistrationRead, status_code=201)
def register_for_event(event_id: UUID, user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> RegistrationRead:
    event = session.scalar(select(Event).options(joinedload(Event.organizer)).where(Event.id == event_id))
    if event is None or event.status != EventStatus.PUBLISHED: raise HTTPException(404, "Событие не найдено")
    if not registration_is_open(event): raise HTTPException(409, "Регистрация уже закрыта")
    if event.capacity is not None:
        active = len([item for item in event.registrations if item.status in {RegistrationStatus.PENDING, RegistrationStatus.APPROVED, RegistrationStatus.ATTENDED}])
        if active >= event.capacity: raise HTTPException(409, "Свободных мест нет")
    registration = EventRegistration(event=event, student=user, status=RegistrationStatus.PENDING if event.requires_approval else RegistrationStatus.APPROVED)
    session.add(registration)
    try: session.commit()
    except IntegrityError as exc:
        session.rollback(); raise HTTPException(409, "Вы уже подавали заявку на это событие") from exc
    return registration_to_read(registration)


@router.get("/registrations/me", response_model=list[RegistrationRead])
def my_registrations(user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> list[RegistrationRead]:
    items = session.scalars(registration_query().where(EventRegistration.student_id == user.id).order_by(EventRegistration.created_at.desc())).unique().all()
    return [registration_to_read(item) for item in items]


@router.post("/registrations/{registration_id}/cancel", response_model=RegistrationRead)
def cancel_registration(registration_id: UUID, user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> RegistrationRead:
    item = session.scalar(registration_query().where(EventRegistration.id == registration_id))
    if item is None: raise HTTPException(404, "Заявка не найдена")
    if item.student_id != user.id: raise HTTPException(403, "Можно отменить только свою заявку")
    try: transition_registration(session, item, RegistrationStatus.CANCELLED)
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    session.commit(); return registration_to_read(item)


@router.get("/events/{event_id}/registrations", response_model=list[RegistrationRead])
def event_registrations(event_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> list[RegistrationRead]:
    event = session.get(Event, event_id)
    if event is None: raise HTTPException(404, "Событие не найдено")
    if event.organizer_id != user.organization_id: raise HTTPException(403, "Нет доступа к заявкам")
    items = session.scalars(registration_query().where(EventRegistration.event_id == event_id).order_by(EventRegistration.created_at.desc())).unique().all()
    return [registration_to_read(item) for item in items]


@router.patch("/registrations/{registration_id}/status", response_model=RegistrationRead)
def update_status(registration_id: UUID, payload: RegistrationStatusUpdate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> RegistrationRead:
    item = session.scalar(registration_query().where(EventRegistration.id == registration_id))
    if item is None: raise HTTPException(404, "Заявка не найдена")
    if item.event.organizer_id != user.organization_id: raise HTTPException(403, "Нет доступа к заявке")
    if payload.status == RegistrationStatus.CANCELLED: raise HTTPException(403, "Отменить заявку может только учащийся")
    try: transition_registration(session, item, payload.status)
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    session.commit(); return registration_to_read(item)
