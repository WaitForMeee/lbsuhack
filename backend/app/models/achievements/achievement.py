import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    registration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("event_registrations.id", ondelete="CASCADE"), unique=True
    )
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text, default="")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    student: Mapped["User"] = relationship()  # noqa: F821
    registration: Mapped["EventRegistration"] = relationship(back_populates="achievement")  # noqa: F821
