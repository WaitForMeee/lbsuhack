from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, choices


class Notification(Identity, Created, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        choices("type", "confirmation deadline interest invite"),
        Index("ix_notification_feed", "student_user_id", "created_at"),
    )
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id")
    )
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(250))
    body: Mapped[str] = mapped_column(Text)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("events.id"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_key: Mapped[str] = mapped_column(String(250), unique=True)
