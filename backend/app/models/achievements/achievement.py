from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, Reviewed, choices


class Achievement(Identity, Created, Reviewed, Base):
    __tablename__ = "achievements"
    __table_args__ = (choices("status", "pending confirmed rejected"),)
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id"), index=True
    )
    title: Mapped[str] = mapped_column(String(250))
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("events.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
