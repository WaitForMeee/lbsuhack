from sqlalchemy import select

from app.models import (
    PartnershipResponse,
)
from app.services.organizations.views import org_view


def response_view(db, r):
    return dict(
        id=r.id,
        request_id=r.request_id,
        school=org_view(db, r.responder_org_id)
        if org_view(db, r.responder_org_id)["kind"] == "school"
        else None,
        organization=org_view(db, r.responder_org_id),
        status=r.status,
        created_at=r.created_at,
        decided_at=r.decided_at,
    )


def partnership_view(db, p, user):
    rows = list(
        db.scalars(
            select(PartnershipResponse)
            .where(PartnershipResponse.request_id == p.id)
            .order_by(PartnershipResponse.created_at, PartnershipResponse.id)
        )
    )
    mine = next((r for r in rows if r.responder_org_id == user.organization_id), None)
    visible = (
        rows
        if user.role == "moderator" or p.sender_org_id == user.organization_id
        else ([mine] if mine else [])
    )
    return dict(
        id=p.id,
        sender=org_view(db, p.sender_org_id),
        target=org_view(db, p.target_org_id),
        visibility=p.visibility,
        title=p.title,
        description=p.description,
        moderation_status=p.moderation_status,
        direct_decision=p.direct_decision,
        responses=[response_view(db, r) for r in visible],
        my_response=response_view(db, mine) if mine else None,
        created_at=p.created_at,
    )
