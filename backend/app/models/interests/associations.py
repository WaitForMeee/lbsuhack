from sqlalchemy import (
    Column,
    ForeignKey,
    Table,
)

from app.db.base import Base

student_interests = Table(
    "student_interests",
    Base.metadata,
    Column(
        "student_user_id",
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("interest_id", ForeignKey("interests.id"), primary_key=True),
)


event_interests = Table(
    "event_interests",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id"), primary_key=True),
)
