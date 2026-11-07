from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.shared.mixins import Created


class FamilyInvitation(Created, Base):
    __tablename__ = "family_invitations"
    parent_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
