"""Insert missing demo records only; existing decisions, dates and passwords survive reruns."""

import hashlib
from datetime import date, timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Achievement,
    Event,
    EventRegistration,
    Interest,
    Notification,
    Organization,
    ParentChild,
    ParentLink,
    PartnershipRequest,
    StudentProfile,
    User,
)
from app.models.shared.mixins import now
from app.services.shared.text import normalize
from app.services.organizations.credentials import issue_token
from app.services.shared.time import today

PASSWORD = "demo1234"
DEMO_ORGANIZATION_TOKENS = {key: "th_demo_" + key + "_" + hashlib.sha256(("talenthub-demo:" + key).encode()).hexdigest() for key in ("school", "company", "school2", "academy")}
INTERESTS = [
    "Математика",
    "Информатика",
    "Физика",
    "Биология",
    "Химия",
    "Робототехника",
    "Проектная работа",
    "Дизайн",
    "Медиа",
    "Экология",
]


def demo_id(key):
    return uuid5(NAMESPACE_URL, "talenthub:v2:demo:" + key)


def insert(db, model, key, **values):
    identity = demo_id(key)
    row = db.get(model, identity)
    if row is None:
        row = model(id=identity, **values)
        db.add(row)
        db.flush()
    return row


def seed_demo(db=None):
    if db is None:
        with SessionLocal.begin() as session:
            return seed_demo(session)
    stamp = today()
    orgs = {}
    for key, kind, name, city in [
        ("school", "school", "Лицей БГУ", "Минск"),
        ("school2", "school", "Гимназия №1 Минск", "Минск"),
        ("school3", "school", "СШ №4 Гродно", "Гродно"),
        ("school4", "school", "Гимназия №2 Брест", "Брест"),
        ("company", "company", "КодМастер", "Минск"),
        ("academy", "academy", "Академия биологии", "Минск"),
        ("robolab", "company", "РобоЛаб", "Гомель"),
        ("chem", "company", "ХимПрактикум", "Гродно"),
        ("nano", "company", "НаноСофт", "Минск"),
    ]:
        orgs[key] = insert(
            db,
            Organization,
            "org:" + key,
            kind=kind,
            name=name,
            city=city,
            description="Образовательные программы для школьников",
            directions=["Информатика"] if kind != "school" else ["Проектная работа"],
        )
    interests = {}
    for name in INTERESTS:
        i = db.scalar(
            select(Interest).where(Interest.normalized_name == normalize(name))
        )
        if i is None:
            i = insert(
                db,
                Interest,
                "interest:" + normalize(name),
                name=name,
                normalized_name=normalize(name),
                is_suggested=True,
            )
        interests[name] = i
    users = {}
    personas = [
        ("alina", "student", "Алина", "Коваль", None),
        ("mark", "student", "Марк", "Левин", None),
        ("olga", "parent", "Ольга", "Коваль", None),
        ("school", "school", "Елена", "Брик", "school"),
        ("company", "company", "Павел", "Мороз", "company"),
        ("admin", "moderator", "Админ", "TalentHub", None),
        ("school2", "school", "Ирина", "Сокол", "school2"),
        ("academy", "company", "Вера", "Мирная", "academy"),
        ("ilya", "student", "Илья", "Савич", None),
        ("maria", "student", "Мария", "Гуд", None),
        ("timofey", "student", "Тимофей", "Орлов", None),
    ]
    password_hash = None
    for key, role, first, last, org in personas:
        if db.get(User, demo_id("user:" + key)) is None and password_hash is None:
            password_hash = hash_password(PASSWORD)
        users[key] = insert(
            db,
            User,
            "user:" + key,
            email=key + "@demo.by",
            password_hash=password_hash or "",
            first_name=first,
            last_name=last,
            role=role,
            organization_id=orgs[org].id if org else None,
        )
        if org and users[key].organization_token_hash is None:
            issue_token(users[key], DEMO_ORGANIZATION_TOKENS[key])
    for key, birthday, org, grade, names in [
        ("alina", date(2010, 4, 12), "school", 10, ["Математика", "Информатика"]),
        ("mark", date(2011, 9, 3), "school2", None, []),
        ("ilya", date(2009, 2, 11), "school", 11, ["Физика"]),
        ("maria", date(2011, 6, 19), "school", 9, ["Биология"]),
        ("timofey", date(2010, 12, 1), "school", 10, ["Робототехника"]),
    ]:
        if db.get(StudentProfile, users[key].id) is None:
            db.add(
                StudentProfile(
                    user_id=users[key].id,
                    birth_date=birthday,
                    school_id=orgs[org].id,
                    grade=grade,
                    city="Минск" if grade else None,
                    interests=[interests[n] for n in names],
                )
            )
    db.flush()
    parent_id, student_id = users["olga"].id, users["alina"].id
    if db.get(ParentChild, (parent_id, student_id)) is None:
        db.add(ParentChild(parent_user_id=parent_id, student_user_id=student_id))
    if db.get(ParentLink, parent_id) is None:
        db.add(ParentLink(parent_user_id=parent_id, student_user_id=student_id))
    db.flush()
    event_specs = [
        (
            "math",
            "Республиканская олимпиада по математике",
            "school",
            "olympiad",
            None,
            ["Математика"],
            14,
            6,
            "published",
        ),
        (
            "code",
            "Олимпиада по информатике «КодБел»",
            "company",
            "olympiad",
            None,
            ["Информатика"],
            26,
            19,
            "published",
        ),
        (
            "physics",
            "Областная олимпиада по физике",
            "school",
            "olympiad",
            None,
            ["Физика"],
            22,
            12,
            "published",
        ),
        (
            "biology",
            "Биологическая интернет-олимпиада",
            "academy",
            "olympiad",
            None,
            ["Биология"],
            39,
            25,
            "published",
        ),
        (
            "chem",
            "Олимпиада «Юный химик»",
            "chem",
            "olympiad",
            None,
            ["Химия"],
            12,
            4,
            "published",
        ),
        (
            "past",
            "Городская олимпиада по математике",
            "school4",
            "olympiad",
            None,
            ["Математика"],
            -7,
            -14,
            "completed",
        ),
        (
            "junior",
            "Олимпиада по информатике для 7–8 классов",
            "company",
            "olympiad",
            None,
            ["Информатика"],
            29,
            22,
            "published",
        ),
        (
            "mathphysics",
            "Открытая олимпиада по физике и математике",
            "school",
            "olympiad",
            None,
            ["Физика", "Математика"],
            34,
            25,
            "published",
        ),
        (
            "engineering",
            "Смена «Инженерные каникулы»",
            "company",
            "project",
            "camp",
            ["Информатика", "Робототехника"],
            24,
            14,
            "published",
        ),
        (
            "research",
            "НПК: конкурс исследовательских проектов",
            "school",
            "project",
            "competition",
            ["Проектная работа", "Биология"],
            36,
            25,
            "published",
        ),
        (
            "robots",
            "Мастерская роботов",
            "robolab",
            "project",
            "workshop",
            ["Робототехника"],
            15,
            8,
            "published",
        ),
        (
            "laboratory",
            "Проектная смена «Физическая лаборатория»",
            "school",
            "project",
            "camp",
            ["Физика", "Проектная работа"],
            30,
            20,
            "published",
        ),
        (
            "design",
            "Конкурс «Математический макет»",
            "school4",
            "project",
            "competition",
            ["Математика", "Дизайн"],
            21,
            12,
            "published",
        ),
        (
            "eco",
            "Смена «Сделай устойчивый город»",
            "company",
            "project",
            "camp",
            ["Экология", "Дизайн"],
            28,
            10,
            "published",
        ),
        (
            "deadline",
            "Медиа о науке",
            "company",
            "project",
            "workshop",
            ["Медиа", "Информатика"],
            2,
            0,
            "published",
        ),
        (
            "pending-school",
            "Олимпиада для выпускников",
            "school",
            "olympiad",
            None,
            ["Математика"],
            44,
            34,
            "pending",
        ),
        (
            "pending-company",
            "Хакатон «Школьный код»",
            "company",
            "project",
            "hackathon",
            ["Информатика", "Проектная работа"],
            16,
            12,
            "pending",
        ),
    ]
    events = {}
    for key, title, org, kind, sub, names, days, deadline, status in event_specs:
        events[key] = insert(
            db,
            Event,
            "event:" + key,
            organizer_id=orgs[org].id,
            title=title,
            description=title
            + ". Образовательная программа для учащихся 7–11 классов.",
            kind=kind,
            project_kind=sub,
            interests=[interests[n] for n in names],
            grade_min=7,
            grade_max=11,
            event_date=stamp + timedelta(days=days),
            registration_deadline=stamp + timedelta(days=deadline),
            city=orgs[org].city,
            venue=orgs[org].name,
            format="online" if key in ("code", "biology") else "offline",
            terms="Участие бесплатно. Регистрация обязательна.",
            capacity=40,
            status=status,
            reviewed_by=users["admin"].id if status != "pending" else None,
            reviewed_at=now() if status != "pending" else None,
        )
    for key, student, event, status, attended in [
        ("math", "alina", "math", "approved", False),
        ("code", "alina", "code", "submitted", False),
        ("past", "alina", "past", "approved", True),
        ("review", "alina", "engineering", "under_review", False),
        ("wait", "alina", "research", "waitlisted", False),
        ("cancel", "alina", "design", "cancelled", False),
        ("reject", "alina", "chem", "rejected", False),
        ("ilya", "ilya", "physics", "submitted", False),
        ("maria", "maria", "biology", "submitted", False),
        ("timofey", "timofey", "robots", "submitted", False),
    ]:
        insert(
            db,
            EventRegistration,
            "registration:" + key,
            event_id=events[event].id,
            student_user_id=users[student].id,
            status=status,
            attended_at=now() - timedelta(days=7) if attended else None,
        )
    for key, title, status in [
        (
            "confirmed",
            "Диплом II степени, городская олимпиада по математике",
            "confirmed",
        ),
        ("pending", "Диплом исследовательской конференции", "pending"),
    ]:
        insert(
            db,
            Achievement,
            "achievement:" + key,
            student_user_id=users["alina"].id,
            title=title,
            status=status,
            event_id=events["past"].id if status == "confirmed" else None,
            reviewed_by=users["admin"].id if status == "confirmed" else None,
            reviewed_at=now() if status == "confirmed" else None,
        )
    for key, sender, target, visibility, title, status in [
        (
            "direct",
            "company",
            "school",
            "direct",
            "Мастер-класс по программированию",
            "approved",
        ),
        (
            "school-request",
            "school",
            "company",
            "direct",
            "Экскурсия для лицеистов",
            "approved",
        ),
        (
            "market",
            "company",
            None,
            "all_schools",
            "Открытая программа для школ",
            "approved",
        ),
        (
            "school-market-mentors",
            "school",
            None,
            "all_companies",
            "Наставники для школьного хакатона",
            "approved",
        ),
        (
            "school-market-lab",
            "school2",
            None,
            "all_companies",
            "Практическая лаборатория для гимназистов",
            "approved",
        ),
        (
            "pending",
            "company",
            "school2",
            "direct",
            "Проектная смена для школьников",
            "pending",
        ),
    ]:
        insert(
            db,
            PartnershipRequest,
            "partnership:" + key,
            sender_org_id=orgs[sender].id,
            target_org_id=orgs[target].id if target else None,
            visibility=visibility,
            title=title,
            description={
                "school-market-mentors": "Лицей БГУ ищет IT-компанию для проведения школьного хакатона: нужны наставники, практические задачи и помощь с оценкой проектов учащихся 9–11 классов.",
                "school-market-lab": "Гимназия №1 Минск приглашает компании и академии провести практические занятия по естественным наукам: нужны эксперты, материалы и совместная программа для учащихся 8–10 классов.",
            }.get(key, "Совместная образовательная инициатива для школьников."),
            moderation_status=status,
            reviewed_by=users["admin"].id if status == "approved" else None,
            reviewed_at=now() if status == "approved" else None,
        )
    for kind, event, title, read in [
        ("confirmation", "math", "Заявка подтверждена", False),
        ("deadline", "deadline", "Напоминание о дедлайне", False),
        ("interest", "mathphysics", "Новое мероприятие по интересам", False),
        ("invite", "junior", "Приглашение на мероприятие", True),
    ]:
        insert(
            db,
            Notification,
            "notification:" + kind,
            student_user_id=users["alina"].id,
            event_id=events[event].id,
            type=kind,
            title=title,
            body=events[event].title,
            source_key="demo:" + kind,
            read_at=now() if read else None,
        )
    db.flush()
    return {"organizations": len(orgs), "users": len(users), "events": len(events)}


def main():
    print(seed_demo())


if __name__ == "__main__":
    main()
