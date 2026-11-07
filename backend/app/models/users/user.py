from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created, Identity, choices


class User(Identity, Created, Base):
    __tablename__ = "users"
    __table_args__ = (
        choices("role", "student parent school company moderator"),
        CheckConstraint(
            "(role IN ('school','company') AND organization_id IS NOT NULL) OR (role NOT IN ('school','company') AND organization_id IS NULL)",
            name="ck_user_organization",
        ),
    )
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    credential_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
