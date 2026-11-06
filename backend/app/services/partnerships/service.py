from sqlalchemy import select

from app.core.errors import fail
from app.models import (
    Organization,
    PartnershipRequest,
    PartnershipResponse,
)
from app.models.shared.mixins import now
from app.services.shared.repository import get


def available(p, user):
    return p.sender_org_id == user.organization_id or (
        p.moderation_status == "approved"
        and (
            p.target_org_id == user.organization_id
            or p.visibility == "all_schools"
            and user.role == "school"
        )
    )


def requests_for(db, user, view="mine"):
    rows = list(
        db.scalars(
            select(PartnershipRequest).order_by(
                PartnershipRequest.created_at.desc(), PartnershipRequest.id
            )
        )
    )
    if view == "marketplace":
        if user.role != "school":
            fail(403, "forbidden", "Рынок предложений доступен школам")
        return [
            p
            for p in rows
            if p.visibility == "all_schools" and p.moderation_status == "approved"
        ]
    response_ids = set(
        db.scalars(
            select(PartnershipResponse.request_id).where(
                PartnershipResponse.school_id == user.organization_id
            )
        )
    )
    return [
        p
        for p in rows
        if p.sender_org_id == user.organization_id
        or p.moderation_status == "approved"
        and (p.target_org_id == user.organization_id or p.id in response_ids)
    ]


def create_request(db, user, data):
    target = db.get(Organization, data.target_org_id) if data.target_org_id else None
    if data.visibility == "all_schools":
        valid = user.role == "company"
    else:
        valid = target and (
            (user.role == "school" and target.kind in ("company", "academy"))
            or (user.role == "company" and target.kind == "school")
        )
    if not valid:
        fail(422, "invalid_partnership_target", "Недопустимое направление запроса")
    p = PartnershipRequest(**data.model_dump(), sender_org_id=user.organization_id)
    db.add(p)
    db.commit()
    return p


def direct_decision(db, identity, user, decision):
    p = get(db, PartnershipRequest, identity, lock=True)
    if (
        p.target_org_id != user.organization_id
        or p.visibility != "direct"
        or p.moderation_status != "approved"
    ):
        fail(404, "not_found", "Запрос не найден")
    if p.direct_decision == decision:
        return p
    if p.direct_decision is not None:
        fail(409, "decision_conflict", "Решение уже принято")
    p.direct_decision = decision
    db.commit()
    return p


def respond(db, identity, user):
    p = get(db, PartnershipRequest, identity, lock=True)
    if p.visibility != "all_schools" or p.moderation_status != "approved":
        fail(404, "not_found", "Предложение не найдено")
    row = db.scalar(
        select(PartnershipResponse).where(
            PartnershipResponse.request_id == p.id,
            PartnershipResponse.school_id == user.organization_id,
        )
    )
    if row is None:
        row = PartnershipResponse(request_id=p.id, school_id=user.organization_id)
        db.add(row)
        db.commit()
    return row


def decide_response(db, identity, user, decision):
    r = get(db, PartnershipResponse, identity, lock=True)
    p = get(db, PartnershipRequest, r.request_id)
    if p.sender_org_id != user.organization_id or p.moderation_status != "approved":
        fail(404, "not_found", "Отклик не найден")
    if r.status == decision:
        return r
    if r.status != "pending":
        fail(409, "decision_conflict", "Решение уже принято")
    r.status = decision
    r.decided_at = now()
    db.commit()
    return r
