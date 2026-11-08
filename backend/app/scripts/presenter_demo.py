"""Private presenter fixtures; plaintext credentials exist only in creation results."""

import secrets
from datetime import date, timedelta

from sqlalchemy import select

from app.core.demo import demo_id
from app.core.security import hash_password
from app.models import (
    Achievement, Event, EventRegistration, Interest, Notification, Organization,
    ParentChild, ParentLink, PartnershipRequest, PartnershipResponse, StudentProfile, User,
)
from app.models.shared.mixins import now
from app.services.organizations.credentials import issue_token
from app.services.shared.time import today

PRESENTER_USERS = {
    "presenter-child1": ("student", "Алексей", "Соколов", None),
    "presenter-child2": ("student", "Дарья", "Соколова", None),
    "presenter-parent": ("parent", "Наталья", "Соколова", None),
    "presenter-school": ("school", "Елена", "Орлова", "presenter-school"),
    "presenter-company": ("company", "Андрей", "Волков", "presenter-company"),
    "presenter-admin": ("moderator", "Модератор", "Презентации", None),
}
PRESENTER_ORGS = ("presenter-school", "presenter-company")


def fresh_credential(user):
    secret = secrets.token_urlsafe(24)
    if user.role in ("school", "company"):
        secret = issue_token(user)
        method = "organization_token"
    else:
        user.password_hash = hash_password(secret)
        method = "password"
    return {"email": user.email, "role": user.role, "method": method, "secret": secret}


def print_credentials(rows):
    if rows:
        print("Закрытые аккаунты: сохраните доступы, повторно показать их невозможно.")
        for row in rows:
            print(f"{row['email']} | {row['role']} | {row['method']} | {row['secret']}")


def seed_presenter(db, *, credential_overrides=None):
    # Import locally: seed_demo invokes this function after creating reference interests.
    from app.scripts.seed_demo import insert

    credentials = []
    overrides = credential_overrides or {}
    orgs = {}
    for key, kind, name in (
        ("presenter-school", "school", "Лицей «Перспектива»"),
        ("presenter-company", "company", "Образовательная компания «Вектор»"),
    ):
        orgs[key] = insert(db, Organization, "org:" + key, kind=kind, name=name,
                          city="Минск", description="Образовательные программы и проекты",
                          directions=["Информатика", "Математика"])
    users = {}
    for key, (role, first, last, org) in PRESENTER_USERS.items():
        user = db.get(User, demo_id("user:" + key))
        if user is None:
            user = User(id=demo_id("user:" + key), email=key + "@demo.by", role=role,
                        first_name=first, last_name=last,
                        organization_id=orgs[org].id if org else None,
                        password_hash=hash_password(secrets.token_urlsafe(32)),
                        credential_version=0)
            if key in overrides:
                for field, value in overrides[key].items():
                    setattr(user, field, value)
            else:
                credentials.append(fresh_credential(user))
            db.add(user)
            db.flush()
        users[key] = user
    interests = list(db.scalars(select(Interest).where(Interest.name.in_(["Информатика", "Математика"]))))
    for index in (1, 2):
        user = users[f"presenter-child{index}"]
        if db.get(StudentProfile, user.id) is None:
            db.add(StudentProfile(user_id=user.id, birth_date=date(2010 + index, 4, 12),
                                  school_id=orgs["presenter-school"].id, grade=11-index,
                                  city="Минск", interests=interests))
    db.flush()
    parent, child = users["presenter-parent"].id, users["presenter-child1"].id
    if db.get(ParentChild, (parent, child)) is None:
        db.add(ParentChild(parent_user_id=parent, student_user_id=child))
    if db.get(ParentLink, parent) is None:
        db.add(ParentLink(parent_user_id=parent, student_user_id=child))

    events = {}
    stamp = today()
    for key, org, status, kind, offset in (
        ("school-open", "presenter-school", "published", "olympiad", 14),
        ("company-open", "presenter-company", "published", "project", 18),
        ("school-pending", "presenter-school", "pending", "olympiad", 24),
        ("company-pending", "presenter-company", "pending", "project", 28),
        ("school-past", "presenter-school", "completed", "olympiad", -7),
        ("company-past", "presenter-company", "completed", "project", -10),
    ):
        title = {
            "school-open": "Олимпиада «Математика будущего»",
            "company-open": "Хакатон «Полезный код»",
            "school-pending": "Лицейская олимпиада по информатике",
            "company-pending": "Практикум «Первый инженерный проект»",
            "school-past": "Городская олимпиада «Логика и числа»",
            "company-past": "Хакатон «Технологии для города»",
        }[key]
        events[key] = insert(
            db, Event, "event:presenter-" + key, organizer_id=orgs[org].id,
            title=title, description=title + ". Образовательная программа для школьников.",
            kind=kind, project_kind="hackathon" if kind == "project" else None,
            interests=interests, grade_min=7, grade_max=11, event_date=stamp+timedelta(days=offset),
            registration_deadline=stamp+timedelta(days=offset-5), city="Минск",
            venue=orgs[org].name, format="offline", terms="Участие бесплатно.",
            capacity=40, status=status,
            reviewed_by=users["presenter-admin"].id if status != "pending" else None,
            reviewed_at=now() if status != "pending" else None,
        )
    for index in (1, 2):
        student = users[f"presenter-child{index}"].id
        for key, status, attended in (
            ("school-open", "submitted" if index == 1 else "approved", False),
            ("company-open", "approved" if index == 1 else "submitted", False),
            ("school-past", "approved", True), ("company-past", "approved", True),
        ):
            insert(db, EventRegistration, f"registration:presenter-{index}-{key}",
                   event_id=events[key].id, student_user_id=student, status=status,
                   attended_at=now()-timedelta(days=7) if attended else None)
        for key, status in (("school-past", "confirmed"), ("company-past", "confirmed"),
                            ("school-pending", "pending")):
            insert(db, Achievement, f"achievement:presenter-{index}-{key}",
                   student_user_id=student, title="Диплом участника: " + events[key].title,
                   event_id=events[key].id, status=status,
                   reviewed_by=users["presenter-admin"].id if status == "confirmed" else None,
                   reviewed_at=now() if status == "confirmed" else None)
        for kind, event, read in (
            ("confirmation", "company-open", False), ("deadline", "school-open", False),
            ("interest", "company-open", False), ("invite", "school-open", True),
        ):
            insert(db, Notification, f"notification:presenter-{index}-{kind}",
                   student_user_id=student, event_id=events[event].id, type=kind,
                   title={"confirmation": "Заявка рассмотрена", "deadline": "Скоро дедлайн",
                          "interest": "Мероприятие по интересам", "invite": "Приглашение на мероприятие"}[kind],
                   body=events[event].title, source_key=f"presenter:{index}:{kind}",
                   read_at=now() if read else None)
    requests = {}
    for key, sender, target, visibility, status in (
        ("school-direct", "presenter-school", "presenter-company", "direct", "approved"),
        ("company-direct", "presenter-company", "presenter-school", "direct", "approved"),
        ("school-market", "presenter-school", None, "all_companies", "approved"),
        ("company-market", "presenter-company", None, "all_schools", "approved"),
        ("pending", "presenter-company", "presenter-school", "direct", "pending"),
    ):
        requests[key] = insert(
            db, PartnershipRequest, "partnership:presenter-" + key,
            sender_org_id=orgs[sender].id, target_org_id=orgs[target].id if target else None,
            visibility=visibility, title="Совместная программа: " + orgs[sender].name,
            description="Наставники, практические занятия и совместные проекты для школьников.",
            moderation_status=status,
            reviewed_by=users["presenter-admin"].id if status == "approved" else None,
            reviewed_at=now() if status == "approved" else None,
        )
    for key, responder in (("school-market", "presenter-company"), ("company-market", "presenter-school")):
        insert(db, PartnershipResponse, "response:presenter-" + key,
               request_id=requests[key].id, responder_org_id=orgs[responder].id, status="pending")
    db.flush()
    return credentials
