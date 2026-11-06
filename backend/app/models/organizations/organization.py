from sqlalchemy import (
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Identity, choices


class Organization(Identity, Base):
    __tablename__ = "organizations"
    __table_args__ = (choices("kind", "school company academy"),)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    directions: Mapped[list[str]] = mapped_column(JSON, default=list)
