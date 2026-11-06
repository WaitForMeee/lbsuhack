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
from app.models.shared.mixins import Created, Identity, choices, now


class EventRegistration(Identity, Created, Base):
    __tablename__ = "event_registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "student_user_id", name="uq_event_student"),
        choices(
            "status", "submitted under_review waitlisted approved rejected cancelled"
        ),
    )
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    attended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )
