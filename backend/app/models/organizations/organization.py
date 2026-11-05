import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrganizationType(str, enum.Enum):
    INSTITUTION = "institution"
    COMPANY = "company"
    ACADEMY = "academy"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="organization_type", native_enum=False)
    )
    description: Mapped[str] = mapped_column(Text, default="")
    region: Mapped[str] = mapped_column(String(120), default="Минск")
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    directions: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    representatives: Mapped[list["User"]] = relationship(back_populates="organization")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="organizer")  # noqa: F821
