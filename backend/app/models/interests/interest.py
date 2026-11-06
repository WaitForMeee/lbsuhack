from sqlalchemy import (
    Boolean,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Identity


class Interest(Identity, Base):
    __tablename__ = "interests"
    name: Mapped[str] = mapped_column(String(100))
    normalized_name: Mapped[str] = mapped_column(String(100), unique=True)
    is_suggested: Mapped[bool] = mapped_column(Boolean, default=False)
