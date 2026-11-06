from fastapi import APIRouter
from sqlalchemy import select

from app.models import (
    Event,
    EventRegistration,
    PartnershipResponse,
    StudentProfile,
    User,
)
from app.routes.shared.dependencies import DB, Organizer, School
from app.schemas.events.responses import EventOut
from app.schemas.organizations.responses import DashboardOut
from app.schemas.shared.base import Items
from app.schemas.students.responses import StudentRow
from app.services.achievements.views import success_view
from app.services.events.views import event_view
from app.services.organizations.views import org_view
from app.services.partnerships.service import requests_for
from app.services.registrations.views import registrations
from app.services.shared.text import normalize
from app.services.users.views import user_view

router = APIRouter(prefix="/organizations/me", tags=["organizations"])


@router.get("/students", response_model=Items[StudentRow])
def students(db: DB, user: School, q: str = ""):
    rows = []
    for p in db.scalars(
        select(StudentProfile)
        .where(StudentProfile.school_id == user.organization_id)
        .order_by(StudentProfile.user_id)
    ):
        u = db.get(User, p.user_id)
        names = [i.name for i in p.interests]
        if normalize(q) not in normalize(
            " ".join([u.first_name, u.last_name, str(p.grade or ""), *names])
        ):
            continue
        success = success_view(db, u.id)
        rows.append(
            dict(
                id=u.id,
                first_name=u.first_name,
                last_name=u.last_name,
                grade=p.grade,
                interests=sorted(names),
                application_count=len(registrations(db, u.id)),
                attendance_count=len(success["attendances"]),
                achievement_count=len(success["achievements"]),
            )
        )
    return dict(items=rows)


@router.get("/events", response_model=Items[EventOut])
def events(db: DB, user: Organizer):
    return dict(
        items=[
            event_view(db, e, user)
            for e in db.scalars(
                select(Event)
                .where(Event.organizer_id == user.organization_id)
                .order_by(Event.created_at.desc(), Event.id)
            )
        ]
    )


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: DB, user: Organizer):
    own = list(
        db.scalars(select(Event).where(Event.organizer_id == user.organization_id))
    )
    event_ids = {e.id for e in own}
    partnerships = requests_for(db, user)
    incoming = [
        p
        for p in partnerships
        if p.target_org_id == user.organization_id and p.direct_decision is None
    ]
    public_ids = {
        p.id
        for p in partnerships
        if p.sender_org_id == user.organization_id and p.visibility == "all_schools"
    }
    responses = (
        list(
            db.scalars(
                select(PartnershipResponse).where(
                    PartnershipResponse.request_id.in_(public_ids)
                )
            )
        )
        if public_ids
        else []
    )
    counters = dict(
        students=len(
            list(
                db.scalars(
                    select(StudentProfile.user_id).where(
                        StudentProfile.school_id == user.organization_id
                    )
                )
            )
        )
        if user.role == "school"
        else 0,
        events=len(own),
        initiatives=len(own),
        published=sum(e.status == "published" for e in own),
        pending_moderation=sum(e.status == "pending" for e in own),
        incoming_requests=len(incoming) + sum(r.status == "pending" for r in responses),
        total_requests=len(partnerships),
        agreed_initiatives=sum(
            p.direct_decision == "accepted"
            or any(r.request_id == p.id and r.status == "accepted" for r in responses)
            for p in partnerships
        ),
        registrations=len(
            list(
                db.scalars(
                    select(EventRegistration.id).where(
                        EventRegistration.event_id.in_(event_ids),
                        EventRegistration.status != "cancelled",
                    )
                )
            )
        )
        if event_ids
        else 0,
    )
    return dict(
        organization=org_view(db, user.organization_id),
        representative=user_view(db, user),
        counters=counters,
    )
