from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import now


class ParentLink(Base):
    __tablename__ = "parent_links"
    parent_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    student_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"), index=True
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
