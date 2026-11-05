import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrestigeEntry(Base):
    __tablename__ = "prestige_entries"
    __table_args__ = (
        UniqueConstraint("organization_id", "partnership_id", name="uq_prestige_org_partnership"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    partnership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("partnerships.id", ondelete="CASCADE"), index=True
    )
    points: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    partnership: Mapped["Partnership"] = relationship(back_populates="prestige_entries")  # noqa: F821
