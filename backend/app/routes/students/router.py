from fastapi import APIRouter

from app.models import StudentProfile
from app.routes.shared.dependencies import DB, Student
from app.schemas.students.requests import ProfileUpdate
from app.schemas.students.responses import ProfileOut, SuccessOut
from app.services.achievements.views import success_view
from app.services.interests.service import resolve_interests
from app.services.organizations.access import school
from app.services.students.views import profile_view

router = APIRouter(prefix="/students/me", tags=["students"])


@router.get("", response_model=ProfileOut)
def profile(db: DB, user: Student):
    return profile_view(db, user.id)


@router.patch("", response_model=ProfileOut)
def update(data: ProfileUpdate, db: DB, user: Student):
    # Serialize replacement of the student's interest set and school.
    p = db.get(StudentProfile, user.id)
    db.refresh(p, with_for_update=True)
    if data.school_id is not None:
        school(db, data.school_id)
        p.school_id = data.school_id
    for key in ("grade", "city"):
        if key in data.model_fields_set:
            setattr(p, key, getattr(data, key))
    if data.interests is not None:
        p.interests = resolve_interests(db, data.interests)
    db.commit()
    return profile_view(db, user.id)


@router.get("/success", response_model=SuccessOut)
def success(db: DB, user: Student):
    return success_view(db, user.id)
