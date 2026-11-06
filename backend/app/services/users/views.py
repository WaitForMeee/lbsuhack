from app.models import StudentProfile
from app.services.students.profile import profile_complete


def user_view(db, u):
    return dict(
        id=u.id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        role=u.role,
        organization_id=u.organization_id,
        profile_complete=profile_complete(db.get(StudentProfile, u.id))
        if u.role == "student"
        else None,
    )
