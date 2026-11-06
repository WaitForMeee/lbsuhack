from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.errors import fail
from app.models import Interest
from app.services.shared.text import normalize


def resolve_interests(db: Session, names: list[str]) -> list[Interest]:
    result = []
    for key, name in {normalize(n): " ".join(n.split()) for n in names}.items():
        if not key:
            fail(422, "invalid_interest", "Пустое направление")
        # PostgreSQL unique index also serializes concurrent creation of a custom interest.
        insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
        db.execute(
            insert(Interest)
            .values(name=name, normalized_name=key, is_suggested=False)
            .on_conflict_do_nothing(index_elements=["normalized_name"])
        )
        result.append(
            db.scalar(select(Interest).where(Interest.normalized_name == key))
        )
    return result
