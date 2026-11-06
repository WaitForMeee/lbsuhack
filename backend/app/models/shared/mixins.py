from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column


def now():
    return datetime.now(UTC)


def choices(column, values):
    return CheckConstraint(
        f"{column} IN ({','.join(repr(v) for v in values.split())})",
        name=f"ck_{column}",
    )


class Identity:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class Created:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Reviewed:
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
