from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, Reviewed, choices


class PartnershipRequest(Identity, Created, Reviewed, Base):
    __tablename__ = "partnership_requests"
    __table_args__ = (
        choices("visibility", "direct all_schools all_companies"),
        choices("moderation_status", "pending approved rejected"),
        CheckConstraint(
            "direct_decision IS NULL OR direct_decision IN ('accepted','declined')",
            name="ck_direct_decision",
        ),
        CheckConstraint(
            "(visibility = 'direct' AND target_org_id IS NOT NULL) OR (visibility IN ('all_schools','all_companies') AND target_org_id IS NULL)",
            name="ck_target",
        ),
        CheckConstraint(
            "target_org_id IS NULL OR sender_org_id != target_org_id",
            name="ck_different_orgs",
        ),
    )
    sender_org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    target_org_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    visibility: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    moderation_status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )
    direct_decision: Mapped[str | None] = mapped_column(String(20))
