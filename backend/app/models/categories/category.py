import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

student_interests = Table(
    "student_interests",
    Base.metadata,
    Column("student_profile_id", ForeignKey("student_profiles.user_id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

event_categories = Table(
    "event_categories",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

    interested_students: Mapped[list["StudentProfile"]] = relationship(  # noqa: F821
        secondary=student_interests, back_populates="interests"
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        secondary=event_categories, back_populates="categories"
    )
