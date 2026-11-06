from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.errors import fail
from app.models import (
    ChildSuggestion,
    Event,
    ParentChild,
    ParentLink,
    StudentProfile,
    User,
)
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Parent
from app.schemas.events.responses import EventOut
from app.schemas.parents.children import ChildrenOut, SuggestionCreate, SuggestionOut
from app.schemas.parents.requests import ChildMatch
from app.schemas.parents.responses import ChildEnvelope
from app.schemas.shared.base import Items
from app.services.events.recommendations import recommendation_cards
from app.services.notifications.service import notify
from app.services.parents.views import child_view
from app.services.shared.repository import get
from app.services.shared.text import normalize

router = APIRouter(prefix="/parents/me", tags=["parents"])


@router.get("/child", response_model=ChildEnvelope)
def child(db: DB, user: Parent):
    link = db.get(ParentLink, user.id)
    return dict(child=child_view(db, link.student_user_id) if link else None)


@router.put("/child", response_model=ChildEnvelope)
def link_child(data: ChildMatch, db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    matches = [
        u
        for u in db.scalars(
            select(User)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(User.role == "student", StudentProfile.birth_date == data.birth_date)
        )
        if normalize(u.first_name) == normalize(data.first_name)
        and normalize(u.last_name) == normalize(data.last_name)
    ]
    if not matches:
        fail(404, "child_not_found", "Ребёнок не найден")
    if len(matches) > 1:
        fail(409, "ambiguous_child", "Найдено несколько учеников")
    link = db.get(ParentLink, user.id)
    if link is None:
        link = ParentLink(parent_user_id=user.id, student_user_id=matches[0].id)
        db.add(link)
    else:
        link.student_user_id = matches[0].id
        link.linked_at = now()
    if db.get(ParentChild, (user.id, link.student_user_id)) is None:
        db.add(
            ParentChild(parent_user_id=user.id, student_user_id=link.student_user_id)
        )
    db.commit()
    return dict(child=child_view(db, link.student_user_id))


@router.get("/children", response_model=ChildrenOut)
def children(db: DB, user: Parent):
    links = list(
        db.scalars(
            select(ParentChild)
            .where(ParentChild.parent_user_id == user.id)
            .order_by(ParentChild.linked_at, ParentChild.student_user_id)
        )
    )
    active = db.get(ParentLink, user.id)
    return dict(
        items=[child_view(db, l.student_user_id) for l in links],
        active_child_id=active.student_user_id if active else None,
    )


@router.post("/children", response_model=ChildEnvelope, status_code=201)
def add_child(data: ChildMatch, db: DB, user: Parent):
    return link_child(data, db, user)


@router.put("/children/{identity}/select", response_model=ChildEnvelope)
def select_child(identity: UUID, db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    if db.get(ParentChild, (user.id, identity)) is None:
        fail(404, "not_found", "Ребёнок не привязан к этому аккаунту")
    active = db.get(ParentLink, user.id)
    if active:
        active.student_user_id = identity
        active.linked_at = now()
    else:
        db.add(ParentLink(parent_user_id=user.id, student_user_id=identity))
    db.commit()
    return dict(child=child_view(db, identity))


def suggestion_view(db, row):
    return dict(
        id=row.id,
        student_user_id=row.student_user_id,
        event_id=row.event_id,
        title=db.get(Event, row.event_id).title,
        created_at=row.created_at,
        status="suggested",
    )


@router.get("/suggestions", response_model=Items[SuggestionOut])
def suggestions(db: DB, user: Parent):
    rows = db.scalars(
        select(ChildSuggestion)
        .where(ChildSuggestion.parent_user_id == user.id)
        .order_by(ChildSuggestion.created_at.desc(), ChildSuggestion.id)
    )
    return dict(items=[suggestion_view(db, row) for row in rows])


@router.post(
    "/children/{identity}/suggestions", response_model=SuggestionOut, status_code=201
)
def suggest(identity: UUID, data: SuggestionCreate, db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    if db.get(ParentChild, (user.id, identity)) is None:
        fail(404, "not_found", "Ребёнок не привязан к этому аккаунту")
    event = get(db, Event, data.event_id)
    if event.status != "published":
        fail(404, "not_found", "Мероприятие не найдено")
    row = db.scalar(
        select(ChildSuggestion).where(
            ChildSuggestion.parent_user_id == user.id,
            ChildSuggestion.student_user_id == identity,
            ChildSuggestion.event_id == event.id,
        )
    )
    if row is None:
        row = ChildSuggestion(
            parent_user_id=user.id, student_user_id=identity, event_id=event.id
        )
        db.add(row)
        db.flush()
        notify(
            db,
            student_id=identity,
            event_id=event.id,
            type="invite",
            title="Родитель предлагает мероприятие",
            body=event.title,
            key=f"parent-suggestion:{row.id}",
        )
        db.commit()
    return suggestion_view(db, row)


@router.get("/children/{identity}/recommendations", response_model=Items[EventOut])
def child_recommendations(
    identity: UUID,
    db: DB,
    user: Parent,
    interest: Annotated[list[str] | None, Query()] = None,
):
    if db.get(ParentChild, (user.id, identity)) is None:
        fail(404, "not_found", "Ребёнок не привязан к этому аккаунту")
    return recommendation_cards(db, db.get(User, identity), interest)
