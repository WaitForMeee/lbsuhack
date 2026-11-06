from typing import Literal
from uuid import UUID

from fastapi import APIRouter

from app.routes.shared.dependencies import DB, Organizer
from app.schemas.partnerships.requests import PartnerDecision, PartnershipCreate
from app.schemas.partnerships.responses import PartnershipOut, PartnershipResponseOut
from app.schemas.shared.base import Items
from app.services.partnerships.service import (
    create_request,
    decide_response,
    direct_decision,
    requests_for,
    respond,
)
from app.services.partnerships.views import partnership_view, response_view

router = APIRouter(tags=["partnerships"])


@router.get("/partnership-requests", response_model=Items[PartnershipOut])
def listing(db: DB, user: Organizer, view: Literal["mine", "marketplace"] = "mine"):
    return dict(
        items=[partnership_view(db, p, user) for p in requests_for(db, user, view)]
    )


@router.post("/partnership-requests", status_code=201, response_model=PartnershipOut)
def create(data: PartnershipCreate, db: DB, user: Organizer):
    return partnership_view(db, create_request(db, user, data), user)


@router.patch(
    "/partnership-requests/{identity}/decision", response_model=PartnershipOut
)
def decide(identity: UUID, data: PartnerDecision, db: DB, user: Organizer):
    return partnership_view(
        db, direct_decision(db, identity, user, data.decision), user
    )


@router.post(
    "/partnership-requests/{identity}/responses",
    status_code=201,
    response_model=PartnershipResponseOut,
)
def response(identity: UUID, db: DB, user: Organizer):
    return response_view(db, respond(db, identity, user))


@router.patch(
    "/partnership-responses/{identity}/decision", response_model=PartnershipResponseOut
)
def response_decision(identity: UUID, data: PartnerDecision, db: DB, user: Organizer):
    return response_view(db, decide_response(db, identity, user, data.decision))
