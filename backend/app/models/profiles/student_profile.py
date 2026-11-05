import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.categories.category import student_interests


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (CheckConstraint("grade >= 1 AND grade <= 11", name="ck_student_grade"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    grade: Mapped[int] = mapped_column(default=10)
    region: Mapped[str] = mapped_column(String(120), default="Минск")
    bio: Mapped[str] = mapped_column(Text, default="")

    user: Mapped["User"] = relationship(back_populates="student_profile")  # noqa: F821
    interests: Mapped[list["Category"]] = relationship(  # noqa: F821
        secondary=student_interests, back_populates="interested_students"
    )
