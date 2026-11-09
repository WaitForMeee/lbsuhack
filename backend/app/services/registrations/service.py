from app.core.demo import DemoRestricted, preview_only
from sqlalchemy import func, select

from app.core.errors import fail
from app.models import (
    Event,
    EventRegistration,
    StudentProfile,
)
from app.models.shared.mixins import now
from app.services.notifications.service import notify
from app.services.shared.repository import get
from app.services.shared.time import today
from app.services.students.profile import profile_complete

ACTIVE = {"submitted", "under_review", "waitlisted", "approved"}


def locked_registration(db, identity, user, *, owner=False):
    r = get(db, EventRegistration, identity)
    e = get(db, Event, r.event_id, lock=True)
    db.refresh(r)
    if (owner and e.organizer_id != user.organization_id) or (
        not owner and r.student_user_id != user.id
    ):
        fail(404, "not_found", "Заявка не найдена")
    return r, e


def apply(db, identity, user):
    e = get(db, Event, identity, lock=True)
    r = db.scalar(
        select(EventRegistration).where(
            EventRegistration.event_id == e.id,
            EventRegistration.student_user_id == user.id,
        )
    )
    if e.status != "published" and r is None:
        fail(404, "not_found", "Мероприятие не найдено")
    # Existing active requests are safe to retry even after registration closes.
    if r and r.status in ACTIVE:
        return r, False
    if not profile_complete(db.get(StudentProfile, user.id)):
        fail(409, "profile_incomplete", "Сначала заполните профиль")
    if e.status != "published" or e.registration_deadline < today():
        fail(409, "registration_unavailable", "Регистрация закрыта")
    if r and r.status == "rejected":
        fail(409, "registration_rejected", "Заявка уже отклонена")
    if r:
        r.status = "submitted"
        r.updated_at = now()
    else:
        r = EventRegistration(event_id=e.id, student_user_id=user.id)
        db.add(r)
    db.commit()
    return r, True


def decide_registration(db, identity, user, decision):
    r, e = locked_registration(db, identity, user, owner=True)
    if r.status == decision:
        return r
    if r.status not in {"submitted", "under_review", "waitlisted"}:
        fail(409, "decision_conflict", "Решение уже принято или заявка отменена")
    if e.status not in {"published", "registration_closed"}:
        fail(409, "event_state_conflict", "Мероприятие не принимает решения по заявкам")
    if decision == "approved":
        count = db.scalar(
            select(func.count())
            .select_from(EventRegistration)
            .where(
                EventRegistration.event_id == e.id,
                EventRegistration.status == "approved",
            )
        )
        if count >= e.capacity:
            fail(409, "capacity_exhausted", "Свободных мест нет")
    if preview_only(user):
        raise DemoRestricted()
    r.status = decision
    # A new submission cycle after cancellation gets its own decision notification.
    key = f"decision:{r.id}:{r.updated_at.isoformat()}:{decision}"
    r.updated_at = now()
    notify(
        db,
        student_id=r.student_user_id,
        event_id=e.id,
        type="confirmation",
        title="Заявка подтверждена" if decision == "approved" else "Заявка отклонена",
        body=e.title,
        key=key,
    )
    db.commit()
    return r


def cancel(db, identity, user):
    r, e = locked_registration(db, identity, user)
    if r.status == "cancelled":
        return r
    if r.status not in ACTIVE or e.status == "completed" or r.attended_at:
        fail(409, "cancellation_unavailable", "Эту заявку нельзя отменить")
    r.status = "cancelled"
    r.updated_at = now()
    db.commit()
    return r


def attend(db, identity, user):
    r, e = locked_registration(db, identity, user, owner=True)
    if r.status != "approved":
        fail(
            409,
            "attendance_unavailable",
            "Посещение доступно подтверждённому участнику",
        )
    if preview_only(user):
        raise DemoRestricted()
    if r.attended_at is None:
        r.attended_at = now()
        db.commit()
    return r
