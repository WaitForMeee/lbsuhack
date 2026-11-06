from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, choices


class PartnershipResponse(Identity, Created, Base):
    __tablename__ = "partnership_responses"
    __table_args__ = (
        UniqueConstraint("request_id", "school_id", name="uq_request_school"),
        choices("status", "pending accepted declined"),
    )
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("partnership_requests.id"), index=True
    )
    school_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
