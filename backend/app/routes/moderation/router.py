from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.errors import fail
from app.models import Achievement, Event, PartnershipRequest, StudentProfile
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Moderator
from app.schemas.events.responses import EventOut
from app.schemas.moderation.requests import ModerationDecision
from app.schemas.moderation.responses import AchievementReview, QueueOut
from app.schemas.partnerships.responses import PartnershipOut
from app.services.events.views import event_view
from app.services.notifications.service import notify
from app.services.partnerships.views import partnership_view
from app.services.shared.repository import get
from app.services.students.views import profile_view

router = APIRouter(prefix="/moderation", tags=["moderation"])


def achievement_view(db, a):
    return dict(
        id=a.id,
        title=a.title,
        event_id=a.event_id,
        status=a.status,
        student=profile_view(db, a.student_user_id),
    )


def section(db, model, column, renderer):
    rows = list(
        db.scalars(
            select(model)
            .where(column == "pending")
            .order_by(model.created_at, model.id)
        )
    )
    return dict(
        items=[renderer(r) for r in rows],
        decided_count=db.scalar(
            select(func.count())
            .select_from(model)
            .where(model.reviewed_at.is_not(None))
        ),
    )


@router.get("/queue", response_model=QueueOut)
def queue(db: DB, user: Moderator):
    return dict(
        events=section(db, Event, Event.status, lambda e: event_view(db, e, user)),
        partnership_requests=section(
            db,
            PartnershipRequest,
            PartnershipRequest.moderation_status,
            lambda p: partnership_view(db, p, user),
        ),
        achievements=section(
            db, Achievement, Achievement.status, lambda a: achievement_view(db, a)
        ),
    )


def review(db, model, identity, user, decision):
    row = get(db, model, identity, lock=True)
    field = "moderation_status" if model is PartnershipRequest else "status"
    target = (
        {
            "Event": "published",
            "PartnershipRequest": "approved",
            "Achievement": "confirmed",
        }[model.__name__]
        if decision == "approve"
        else "rejected"
    )
    # reviewed_at survives lifecycle changes, so retrying approve after completion remains idempotent.
    if row.reviewed_at is not None:
        approved = getattr(row, field) != "rejected"
        if approved == (decision == "approve"):
            return row
        fail(409, "decision_conflict", "Решение модератора уже принято")
    if getattr(row, field) != "pending":
        fail(409, "decision_conflict", "Запись уже рассмотрена")
    setattr(row, field, target)
    row.reviewed_by = user.id
    row.reviewed_at = now()
    if model is Event and decision == "approve":
        keys = {i.id for i in row.interests}
        for p in db.scalars(select(StudentProfile)):
            if keys.intersection(i.id for i in p.interests):
                notify(
                    db,
                    student_id=p.user_id,
                    event_id=row.id,
                    type="interest",
                    title="Новое мероприятие по интересам",
                    body=row.title,
                    key=f"publication:{row.id}:{p.user_id}",
                )
    db.commit()
    return row


@router.post("/events/{identity}/decision", response_model=EventOut)
def event_decision(identity: UUID, data: ModerationDecision, db: DB, user: Moderator):
    return event_view(db, review(db, Event, identity, user, data.decision), user)


@router.post("/partnership-requests/{identity}/decision", response_model=PartnershipOut)
def partnership_decision(
    identity: UUID, data: ModerationDecision, db: DB, user: Moderator
):
    return partnership_view(
        db, review(db, PartnershipRequest, identity, user, data.decision), user
    )


@router.post("/achievements/{identity}/decision", response_model=AchievementReview)
def achievement_decision(
    identity: UUID, data: ModerationDecision, db: DB, user: Moderator
):
    return achievement_view(db, review(db, Achievement, identity, user, data.decision))
