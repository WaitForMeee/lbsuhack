from app.routes.shared.router import APIRouter
from uuid import UUID

from fastapi import Response
from sqlalchemy import select

from app.core.demo import demo_preview
from app.models import EventRegistration, StudentProfile, User
from app.routes.shared.dependencies import DB, Organizer, Student
from app.schemas.registrations.requests import RegistrationDecision
from app.schemas.registrations.responses import ParticipantOut, RegistrationOut
from app.schemas.shared.base import Items
from app.services.events.service import owned_event
from app.services.registrations.service import (
    apply,
    attend,
    cancel,
    decide_registration,
)
from app.services.registrations.views import registration_view, registrations

router = APIRouter(tags=["registrations"])


@router.post(
    "/events/{identity}/registrations",
    response_model=RegistrationOut,
    status_code=201,
    responses={200: {"model": RegistrationOut}},
)
def register(identity: UUID, response: Response, db: DB, user: Student):
    row, created = apply(db, identity, user)
    response.status_code = 201 if created else 200
    return registration_view(db, row)


@router.get("/registrations/me", response_model=Items[RegistrationOut])
def mine(db: DB, user: Student):
    return dict(items=[registration_view(db, r) for r in registrations(db, user.id)])


@router.post("/registrations/{identity}/cancel", response_model=RegistrationOut)
def cancel_registration(identity: UUID, db: DB, user: Student):
    return registration_view(db, cancel(db, identity, user))


@router.get("/events/{identity}/registrations", response_model=Items[ParticipantOut])
def participants(identity: UUID, db: DB, user: Organizer):
    owned_event(db, identity, user)
    result = []
    for r in db.scalars(
        select(EventRegistration)
        .where(
            EventRegistration.event_id == identity,
            EventRegistration.status != "cancelled",
        )
        .order_by(EventRegistration.created_at, EventRegistration.id)
    ):
        student = db.get(User, r.student_user_id)
        p = db.get(StudentProfile, student.id)
        result.append(
            dict(
                **registration_view(db, r),
                first_name=student.first_name,
                last_name=student.last_name,
                grade=p.grade,
            )
        )
    return dict(items=result)


@router.patch("/registrations/{identity}/decision", response_model=RegistrationOut)
@demo_preview
def decide(identity: UUID, data: RegistrationDecision, db: DB, user: Organizer):
    return registration_view(db, decide_registration(db, identity, user, data.decision))


@router.put("/registrations/{identity}/attendance", response_model=RegistrationOut)
@demo_preview
def attendance(identity: UUID, db: DB, user: Organizer):
    return registration_view(db, attend(db, identity, user))
