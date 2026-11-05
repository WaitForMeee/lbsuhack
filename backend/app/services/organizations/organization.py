from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.events.event import Event, EventStatus
from app.models.organizations.organization import Organization
from app.models.prestige.prestige import PrestigeEntry
from app.schemas.organizations.organization import OrganizationRead, PrestigeEntryRead


def organization_to_read(session: Session, organization: Organization) -> OrganizationRead:
    entries = list(
        session.scalars(
            select(PrestigeEntry)
            .where(PrestigeEntry.organization_id == organization.id)
            .order_by(PrestigeEntry.created_at.desc())
        ).all()
    )
    published_count = session.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.organizer_id == organization.id, Event.status == EventStatus.PUBLISHED)
    ) or 0
    return OrganizationRead(
        id=organization.id,
        name=organization.name,
        type=organization.type,
        description=organization.description,
        region=organization.region,
        contact_email=organization.contact_email,
        website_url=organization.website_url,
        directions=organization.directions,
        prestige_score=sum(entry.points for entry in entries),
        prestige_history=[
            PrestigeEntryRead(
                id=entry.id,
                points=entry.points,
                reason=entry.reason,
                created_at=entry.created_at,
            )
            for entry in entries
        ],
        published_event_count=published_count,
    )
