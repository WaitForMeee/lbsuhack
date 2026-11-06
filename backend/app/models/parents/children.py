from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, now


class ParentChild(Base):
    __tablename__ = "parent_children"
    parent_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ChildSuggestion(Identity, Created, Base):
    __tablename__ = "child_suggestions"
    __table_args__ = (
        UniqueConstraint(
            "parent_user_id",
            "student_user_id",
            "event_id",
            name="uq_parent_child_event",
        ),
    )
    parent_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
