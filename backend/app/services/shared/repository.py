from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import fail


def get(db: Session, model, identity: UUID, *, lock=False):
    stmt = select(model).where(model.id == identity)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    obj = db.scalar(stmt)
    if obj is None:
        fail(404, "not_found", "Запись не найдена")
    return obj
