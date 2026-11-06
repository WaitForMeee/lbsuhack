from datetime import date
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.interests.associations import event_interests
from app.models.interests.interest import Interest
from app.models.shared.mixins import Created, Identity, Reviewed, choices


class Event(Identity, Created, Reviewed, Base):
    __tablename__ = "events"
    __table_args__ = (
        choices("kind", "olympiad project"),
        choices("format", "offline online hybrid"),
        choices("status", "pending published rejected registration_closed completed"),
        CheckConstraint("capacity > 0", name="ck_capacity"),
        CheckConstraint(
            "7 <= grade_min AND grade_min <= grade_max AND grade_max <= 11",
            name="ck_grade_range",
        ),
        CheckConstraint("registration_deadline <= event_date", name="ck_deadline"),
        CheckConstraint(
            "kind = 'project' OR project_kind IS NULL", name="ck_project_kind"
        ),
        Index("ix_events_catalog", "status", "event_date"),
    )
    organizer_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))
    project_kind: Mapped[str | None] = mapped_column(String(100))
    grade_min: Mapped[int]
    grade_max: Mapped[int]
    event_date: Mapped[date]
    registration_deadline: Mapped[date]
    city: Mapped[str] = mapped_column(String(100))
    venue: Mapped[str] = mapped_column(String(250))
    format: Mapped[str] = mapped_column(String(20))
    terms: Mapped[str] = mapped_column(Text)
    capacity: Mapped[int]
    status: Mapped[str] = mapped_column(String(30), default="pending")
    interests: Mapped[list[Interest]] = relationship(
        secondary=event_interests, lazy="selectin"
    )
