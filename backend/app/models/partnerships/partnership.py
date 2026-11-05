import enum
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OpportunityDirection(str, enum.Enum):
    INSTITUTION_SEEKS_ORGANIZATION = "institution_seeks_organization"
    ORGANIZATION_SEEKS_INSTITUTION = "organization_seeks_institution"


class OpportunityStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ResponseStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PartnershipStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class PartnershipOpportunity(Base):
    __tablename__ = "partnership_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creator_organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    target_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    direction: Mapped[OpportunityDirection] = mapped_column(
        Enum(OpportunityDirection, name="opportunity_direction", native_enum=False), index=True
    )
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(180))
    format: Mapped[str] = mapped_column(String(120))
    target_audience: Mapped[str] = mapped_column(String(300))
    conditions: Mapped[str] = mapped_column(Text, default="")
    desired_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    desired_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, name="opportunity_status", native_enum=False),
        default=OpportunityStatus.OPEN,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    creator_organization: Mapped["Organization"] = relationship(foreign_keys=[creator_organization_id])  # noqa: F821
    target_organization: Mapped["Organization | None"] = relationship(foreign_keys=[target_organization_id])  # noqa: F821
    responses: Mapped[list["PartnershipResponse"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    partnership: Mapped["Partnership | None"] = relationship(back_populates="opportunity", uselist=False)


class PartnershipResponse(Base):
    __tablename__ = "partnership_responses"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "responder_organization_id", name="uq_opportunity_responder"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partnership_opportunities.id", ondelete="CASCADE"), index=True
    )
    responder_organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ResponseStatus] = mapped_column(
        Enum(ResponseStatus, name="partnership_response_status", native_enum=False),
        default=ResponseStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    opportunity: Mapped[PartnershipOpportunity] = relationship(back_populates="responses")
    responder_organization: Mapped["Organization"] = relationship()  # noqa: F821
    partnership: Mapped["Partnership | None"] = relationship(back_populates="accepted_response", uselist=False)


class Partnership(Base):
    __tablename__ = "partnerships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partnership_opportunities.id", ondelete="CASCADE"), unique=True
    )
    accepted_response_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partnership_responses.id", ondelete="CASCADE"), unique=True
    )
    organization_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    organization_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    organization_a_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_b_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[PartnershipStatus] = mapped_column(
        Enum(PartnershipStatus, name="partnership_status", native_enum=False),
        default=PartnershipStatus.ACTIVE,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    opportunity: Mapped[PartnershipOpportunity] = relationship(back_populates="partnership")
    accepted_response: Mapped[PartnershipResponse] = relationship(back_populates="partnership")
    organization_a: Mapped["Organization"] = relationship(foreign_keys=[organization_a_id])  # noqa: F821
    organization_b: Mapped["Organization"] = relationship(foreign_keys=[organization_b_id])  # noqa: F821
    prestige_entries: Mapped[list["PrestigeEntry"]] = relationship(  # noqa: F821
        back_populates="partnership", cascade="all, delete-orphan"
    )
