from app.models import StudentProfile


def profile_complete(p: StudentProfile | None) -> bool:
    return bool(p and p.grade and p.city and p.interests)
