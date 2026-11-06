from app.models import (
    Organization,
    StudentProfile,
    User,
)
from app.services.students.profile import profile_complete


def profile_view(db, identity):
    u = db.get(User, identity)
    p = db.get(StudentProfile, identity)
    school = db.get(Organization, p.school_id)
    return dict(
        id=u.id,
        first_name=u.first_name,
        last_name=u.last_name,
        birth_date=p.birth_date,
        school=dict(id=school.id, name=school.name),
        grade=p.grade,
        city=p.city,
        interests=sorted(i.name for i in p.interests),
        profile_complete=profile_complete(p),
    )
