from datetime import date
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.interests.associations import student_interests
from app.models.interests.interest import Interest


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        CheckConstraint("grade IS NULL OR grade BETWEEN 7 AND 11", name="ck_grade"),
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    birth_date: Mapped[date]
    school_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    grade: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100))
    interests: Mapped[list[Interest]] = relationship(
        secondary=student_interests, lazy="selectin"
    )
