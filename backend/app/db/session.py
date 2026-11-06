from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.engine import create_database_engine

settings = get_settings()
engine = create_database_engine(settings.database_url, settings.database_schema)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
