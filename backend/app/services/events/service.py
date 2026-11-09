from app.core.demo import DemoRestricted, preview_only
from app.core.errors import fail
from app.models import (
    Event,
)
from app.services.shared.repository import get
from app.services.shared.time import today


def owned_event(db, identity, user, *, lock=False):
    event = get(db, Event, identity, lock=lock)
    if event.organizer_id != user.organization_id:
        fail(404, "not_found", "Мероприятие не найдено")
    return event


def transition(db, identity, user, target):
    e = owned_event(db, identity, user, lock=True)
    if e.status == target:
        return e
    allowed = {
        "registration_closed": {"published"},
        "published": {"registration_closed"},
        "completed": {"published", "registration_closed"},
    }
    if e.status not in allowed[target]:
        fail(409, "event_state_conflict", "Недопустимый переход состояния")
    if target == "published" and e.registration_deadline < today():
        fail(409, "deadline_expired", "Дедлайн регистрации истёк")
    if preview_only(user):
        raise DemoRestricted()
    e.status = target
    db.commit()
    return e
