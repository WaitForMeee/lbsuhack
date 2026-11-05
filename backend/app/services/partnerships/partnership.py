from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import PRESTIGE_POINTS_PER_PARTNERSHIP

from app.models.partnerships.partnership import (
    OpportunityStatus,
    Partnership,
    PartnershipOpportunity,
    PartnershipResponse,
    PartnershipStatus,
    ResponseStatus,
)
from app.models.prestige.prestige import PrestigeEntry
from app.schemas.partnerships.partnership import (
    OpportunityRead,
    OrganizationBrief,
    PartnershipRead,
    ResponseRead,
)


def organization_brief(session: Session, organization) -> OrganizationBrief:
    score = session.scalar(
        select(func.coalesce(func.sum(PrestigeEntry.points), 0)).where(
            PrestigeEntry.organization_id == organization.id
        )
    ) or 0
    return OrganizationBrief(
        id=organization.id,
        name=organization.name,
        type=organization.type.value,
        prestige_score=score,
    )


def opportunity_to_read(session: Session, opportunity: PartnershipOpportunity) -> OpportunityRead:
    return OpportunityRead(
        id=opportunity.id,
        creator=organization_brief(session, opportunity.creator_organization),
        target=(organization_brief(session, opportunity.target_organization) if opportunity.target_organization else None),
        direction=opportunity.direction,
        title=opportunity.title,
        description=opportunity.description,
        topic=opportunity.topic,
        format=opportunity.format,
        target_audience=opportunity.target_audience,
        conditions=opportunity.conditions,
        desired_start=opportunity.desired_start,
        desired_end=opportunity.desired_end,
        status=opportunity.status,
        created_at=opportunity.created_at,
        responses=[
            ResponseRead(
                id=response.id,
                responder=organization_brief(session, response.responder_organization),
                message=response.message,
                status=response.status,
                created_at=response.created_at,
            )
            for response in opportunity.responses
        ],
    )


def partnership_to_read(session: Session, partnership: Partnership) -> PartnershipRead:
    return PartnershipRead(
        id=partnership.id,
        title=partnership.opportunity.title,
        organization_a=organization_brief(session, partnership.organization_a),
        organization_b=organization_brief(session, partnership.organization_b),
        organization_a_confirmed=partnership.organization_a_confirmed,
        organization_b_confirmed=partnership.organization_b_confirmed,
        status=partnership.status,
        completed_at=partnership.completed_at,
        created_at=partnership.created_at,
    )


def accept_response(session: Session, response: PartnershipResponse) -> Partnership:
    opportunity = response.opportunity
    if opportunity.status != OpportunityStatus.OPEN or response.status != ResponseStatus.PENDING:
        raise ValueError("Этот отклик уже нельзя принять")
    response.status = ResponseStatus.ACCEPTED
    for other in opportunity.responses:
        if other.id != response.id and other.status == ResponseStatus.PENDING:
            other.status = ResponseStatus.REJECTED
    opportunity.status = OpportunityStatus.CLOSED
    partnership = Partnership(
        opportunity=opportunity,
        accepted_response=response,
        organization_a_id=opportunity.creator_organization_id,
        organization_b_id=response.responder_organization_id,
    )
    session.add(partnership)
    session.flush()
    return partnership


def confirm_partnership(session: Session, partnership: Partnership, organization_id) -> None:
    if partnership.status == PartnershipStatus.COMPLETED:
        return
    if organization_id == partnership.organization_a_id:
        partnership.organization_a_confirmed = True
    elif organization_id == partnership.organization_b_id:
        partnership.organization_b_confirmed = True
    else:
        raise PermissionError("Организация не участвует в партнёрстве")
    if partnership.organization_a_confirmed and partnership.organization_b_confirmed:
        partnership.status = PartnershipStatus.COMPLETED
        partnership.completed_at = datetime.now(UTC)
        for organization in (partnership.organization_a, partnership.organization_b):
            existing = session.scalar(
                select(PrestigeEntry).where(
                    PrestigeEntry.organization_id == organization.id,
                    PrestigeEntry.partnership_id == partnership.id,
                )
            )
            if existing is None:
                session.add(
                    PrestigeEntry(
                        organization_id=organization.id,
                        partnership_id=partnership.id,
                        points=PRESTIGE_POINTS_PER_PARTNERSHIP,
                        reason=f"Подтверждённая совместная инициатива «{partnership.opportunity.title}»",
                    )
                )
    session.flush()
