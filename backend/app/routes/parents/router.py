from app.routes.shared.router import APIRouter
from typing import Annotated
from uuid import UUID

from fastapi import Query
from sqlalchemy import select

from app.core.errors import fail
from app.models import (
    ChildSuggestion,
    Event,
    ParentChild,
    ParentLink,
    User,
)
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Parent
from app.schemas.events.responses import EventOut
from app.schemas.parents.children import ChildrenOut, SuggestionCreate, SuggestionOut
from app.schemas.parents.responses import ChildEnvelope
from app.schemas.shared.base import Items
from app.services.events.recommendations import recommendation_cards
from app.services.notifications.service import notify
from app.services.parents.views import child_view
from app.services.shared.repository import get

from app.models import FamilyInvitation
from app.schemas.auth.access import InvitationEnvelope
from app.services.parents.invitations import invitation_view

router = APIRouter(prefix="/parents/me", tags=["parents"])


@router.get("/child", response_model=ChildEnvelope)
def child(db: DB, user: Parent):
    link = db.get(ParentLink, user.id)
    return dict(child=child_view(db, link.student_user_id) if link else None)


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


@router.get("/invitation", response_model=InvitationEnvelope)
def get_invitation(db: DB, user: Parent):
    return invitation_view(db.get(FamilyInvitation, user.id))


@router.post("/invitation", response_model=InvitationEnvelope)
def create_invitation(db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    invitation = db.get(FamilyInvitation, user.id)
    if invitation is None:
        invitation = FamilyInvitation(parent_user_id=user.id)
        db.add(invitation)
        db.flush()
    result = invitation_view(invitation)
    db.commit()
    return result


@router.delete("/invitation", response_model=InvitationEnvelope)
def delete_invitation(db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    invitation = db.get(FamilyInvitation, user.id)
    if invitation is not None:
        db.delete(invitation)
    db.commit()
    return {"invitation": None}
