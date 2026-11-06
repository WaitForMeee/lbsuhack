from app.services.achievements.views import success_view
from app.services.registrations.views import registration_view, registrations
from app.services.students.views import profile_view


def child_view(db, identity):
    return dict(
        profile=profile_view(db, identity),
        applications=[registration_view(db, r) for r in registrations(db, identity)],
        **success_view(db, identity),
    )
