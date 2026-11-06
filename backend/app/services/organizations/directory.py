from collections import defaultdict

from sqlalchemy import select

from app.models import (
    Achievement,
    Event,
    Organization,
    PartnershipRequest,
    PartnershipResponse,
    StudentProfile,
)
from app.services.organizations.views import org_view
from app.services.shared.text import normalize


def school_directory(db, q=""):
    schools = list(
        db.scalars(
            select(Organization)
            .where(Organization.kind == "school")
            .order_by(Organization.name, Organization.id)
        )
    )
    events = {e.id: e for e in db.scalars(select(Event))}
    profiles = {p.user_id: p for p in db.scalars(select(StudentProfile))}
    achievements = list(
        db.scalars(select(Achievement).where(Achievement.status == "confirmed"))
    )
    partnerships = list(
        db.scalars(
            select(PartnershipRequest).where(
                PartnershipRequest.moderation_status == "approved"
            )
        )
    )
    responses = list(
        db.scalars(
            select(PartnershipResponse).where(PartnershipResponse.status == "accepted")
        )
    )
    result = []
    for school in schools:
        if normalize(q) not in normalize(school.name + " " + school.city):
            continue
        own_achievements = [
            a
            for a in achievements
            if profiles[a.student_user_id].school_id == school.id
        ]
        groups = defaultdict(list)
        for a in own_achievements:
            event = events.get(a.event_id)
            if event is None:
                continue
            direction = (
                "олимпиады"
                if event.kind == "olympiad"
                else "хакатоны"
                if event.project_kind == "hackathon"
                else "проектная деятельность"
            )
            for interest in event.interests:
                groups[(interest.name, direction)].append(a)
        indicators = []
        for (subject, direction), rows in sorted(groups.items()):
            dates = [(a.reviewed_at or a.created_at).date() for a in rows]
            years = sorted({d.year for d in dates})
            indicators.append(
                dict(
                    subject=subject,
                    direction=direction,
                    count=len(rows),
                    criterion="Подтверждённые достижения учащихся по связанным мероприятиям",
                    source="Подтверждения модератора TalentHub",
                    period=str(years[0])
                    if len(years) == 1
                    else f"{years[0]}–{years[-1]}",
                    level="Уровень не указан",
                    updated=max(dates),
                )
            )
        partner_ids = set()
        for request in partnerships:
            if request.direct_decision == "accepted":
                if request.sender_org_id == school.id:
                    partner_ids.add(request.target_org_id)
                if request.target_org_id == school.id:
                    partner_ids.add(request.sender_org_id)
            for response in responses:
                if response.request_id != request.id:
                    continue
                if response.responder_org_id == school.id:
                    partner_ids.add(request.sender_org_id)
                if request.sender_org_id == school.id:
                    partner_ids.add(response.responder_org_id)
        own_events = [
            e
            for e in events.values()
            if e.organizer_id == school.id
            and e.status in ("published", "registration_closed", "completed")
        ]
        years = defaultdict(int)
        for a in own_achievements:
            years[(a.reviewed_at or a.created_at).year] += 1
        result.append(
            dict(
                **org_view(db, school.id),
                region=school.city,
                programs=[e.title for e in own_events if e.kind == "project"],
                partnerships=sorted(
                    db.get(Organization, id).name for id in partner_ids if id
                ),
                events=[e.title for e in own_events],
                achievements=[a.title for a in own_achievements],
                history=[
                    f"{year} — подтверждённых достижений: {count}"
                    for year, count in sorted(years.items(), reverse=True)
                ],
                indicators=indicators,
                gap=""
                if indicators
                else "Недостаточно подтверждённых данных. Это не означает, что школа слабее остальных.",
            )
        )
    return result
