from fastapi import APIRouter
from sqlalchemy import select

from app.core.errors import fail
from app.models import ParentLink, StudentProfile, User
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Parent
from app.schemas.parents.requests import ChildMatch
from app.schemas.parents.responses import ChildEnvelope
from app.services.parents.views import child_view
from app.services.shared.text import normalize

router = APIRouter(prefix="/parents/me/child", tags=["parents"])


@router.get("", response_model=ChildEnvelope)
def child(db: DB, user: Parent):
    link = db.get(ParentLink, user.id)
    return dict(child=child_view(db, link.student_user_id) if link else None)


@router.put("", response_model=ChildEnvelope)
def link_child(data: ChildMatch, db: DB, user: Parent):
    db.refresh(user, with_for_update=True)
    matches = [
        u
        for u in db.scalars(
            select(User)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(User.role == "student", StudentProfile.birth_date == data.birth_date)
        )
        if normalize(u.first_name) == normalize(data.first_name)
        and normalize(u.last_name) == normalize(data.last_name)
    ]
    if not matches:
        fail(404, "child_not_found", "Ребёнок не найден")
    if len(matches) > 1:
        fail(409, "ambiguous_child", "Найдено несколько учеников")
    link = db.get(ParentLink, user.id)
    if link is None:
        link = ParentLink(parent_user_id=user.id, student_user_id=matches[0].id)
        db.add(link)
    else:
        link.student_user_id = matches[0].id
        link.linked_at = now()
    db.commit()
    return dict(child=child_view(db, link.student_user_id))
