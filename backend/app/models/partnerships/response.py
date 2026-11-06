from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, synonym

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, choices


class PartnershipResponse(Identity, Created, Base):
    __tablename__ = "partnership_responses"
    __table_args__ = (
        UniqueConstraint(
            "request_id", "responder_org_id", name="uq_request_organization"
        ),
        choices("status", "pending accepted declined"),
    )
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("partnership_requests.id"), index=True
    )
    responder_org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Compatibility alias for existing application/fixture imports.
    school_id = synonym("responder_org_id")
