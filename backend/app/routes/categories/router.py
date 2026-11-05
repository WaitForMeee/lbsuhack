from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.categories.category import Category
from app.schemas.profiles.profile import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(session: Annotated[Session, Depends(get_db_session)]) -> list[CategoryRead]:
    return [CategoryRead.model_validate(item, from_attributes=True) for item in session.scalars(select(Category).order_by(Category.name))]
