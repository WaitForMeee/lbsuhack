from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import fail
from app.models import Organization


def school(db: Session, identity: UUID):
    obj = db.get(Organization, identity)
    if obj is None or obj.kind != "school":
        fail(422, "invalid_school", "Выберите школу из справочника")
    return obj
