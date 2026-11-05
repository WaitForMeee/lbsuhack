from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db_session
from app.models.achievements.achievement import Achievement
from app.models.categories.category import Category
from app.models.profiles.student_profile import StudentProfile
from app.models.registrations.registration import EventRegistration
from app.models.events.event import Event
from app.routes.auth.dependencies import StudentUser
from app.schemas.profiles.profile import AchievementRead, CategoryRead, InterestsUpdate, StudentProfileRead, StudentProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


def profile_read(profile: StudentProfile) -> StudentProfileRead:
    return StudentProfileRead(
        user_id=profile.user_id, full_name=profile.user.full_name, email=profile.user.email,
        grade=profile.grade, region=profile.region, bio=profile.bio,
        interests=[CategoryRead.model_validate(item, from_attributes=True) for item in profile.interests],
    )


@router.get("/me", response_model=StudentProfileRead)
def get_profile(user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> StudentProfileRead:
    profile = session.scalar(select(StudentProfile).options(joinedload(StudentProfile.user), selectinload(StudentProfile.interests)).where(StudentProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(404, "Профиль не найден")
    return profile_read(profile)


@router.put("/me", response_model=StudentProfileRead)
def update_profile(payload: StudentProfileUpdate, user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> StudentProfileRead:
    profile = session.scalar(select(StudentProfile).options(joinedload(StudentProfile.user), selectinload(StudentProfile.interests)).where(StudentProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(404, "Профиль не найден")
    profile.user.full_name = payload.full_name
    profile.grade, profile.region, profile.bio = payload.grade, payload.region, payload.bio
    session.commit(); session.refresh(profile)
    return profile_read(profile)


@router.put("/me/interests", response_model=StudentProfileRead)
def update_interests(payload: InterestsUpdate, user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> StudentProfileRead:
    profile = session.scalar(select(StudentProfile).options(joinedload(StudentProfile.user), selectinload(StudentProfile.interests)).where(StudentProfile.user_id == user.id))
    categories = list(session.scalars(select(Category).where(Category.id.in_(payload.category_ids))).all())
    if profile is None or len(categories) != len(set(payload.category_ids)):
        raise HTTPException(400, "Некорректный профиль или категории")
    profile.interests = categories
    session.commit()
    return profile_read(profile)


@router.get("/me/portfolio", response_model=list[AchievementRead])
def portfolio(user: StudentUser, session: Annotated[Session, Depends(get_db_session)]) -> list[AchievementRead]:
    items = session.scalars(select(Achievement).options(joinedload(Achievement.registration).joinedload(EventRegistration.event).joinedload(Event.organizer)).where(Achievement.student_id == user.id).order_by(Achievement.issued_at.desc())).all()
    return [AchievementRead(id=item.id, title=item.title, description=item.description, issued_at=item.issued_at, event_id=item.registration.event.id, event_slug=item.registration.event.slug, event_image_url=item.registration.event.image_url, organizer_name=item.registration.event.organizer.name) for item in items]
