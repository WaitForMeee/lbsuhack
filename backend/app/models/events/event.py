import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.categories.category import event_categories


class EventFormat(str, enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    organizer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), index=True)
    summary: Mapped[str] = mapped_column(String(400))
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    format: Mapped[EventFormat] = mapped_column(Enum(EventFormat, name="event_format", native_enum=False))
    region: Mapped[str] = mapped_column(String(120), default="Минск", index=True)
    venue: Mapped[str | None] = mapped_column(String(220), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    target_audience: Mapped[str] = mapped_column(String(500), default="Учащиеся лицеев")
    min_grade: Mapped[int] = mapped_column(Integer, default=7)
    max_grade: Mapped[int] = mapped_column(Integer, default=11)
    participation_terms: Mapped[str] = mapped_column(Text, default="")
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status", native_enum=False), default=EventStatus.DRAFT, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    organizer: Mapped["Organization"] = relationship(back_populates="events")  # noqa: F821
    categories: Mapped[list["Category"]] = relationship(  # noqa: F821
        secondary=event_categories, back_populates="events"
    )
    registrations: Mapped[list["EventRegistration"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
