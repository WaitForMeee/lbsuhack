"""Idempotent, non-destructive demo dataset for the complete milestone."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.constants import PRESTIGE_POINTS_PER_PARTNERSHIP
from app.db.session import SessionLocal
from app.models.achievements.achievement import Achievement
from app.models.categories.category import Category
from app.models.events.event import Event, EventFormat, EventStatus
from app.models.organizations.organization import Organization, OrganizationType
from app.models.partnerships.partnership import OpportunityDirection, OpportunityStatus, Partnership, PartnershipOpportunity, PartnershipResponse, PartnershipStatus, ResponseStatus
from app.models.prestige.prestige import PrestigeEntry
from app.models.profiles.student_profile import StudentProfile
from app.models.registrations.registration import EventRegistration, RegistrationStatus
from app.models.users.user import User, UserRole
from app.scripts.seed_helpers import SeedUser, create_user_if_missing, get_or_create_organization


@dataclass(frozen=True)
class MockOrganization:
    name: str
    type: OrganizationType
    description: str
    representative_email: str
    representative_name: str


MOCK_ORGANIZATIONS = (
    MockOrganization("Лицей «Горизонт»", OrganizationType.INSTITUTION, "Городской лицей с инженерным и естественно-научным направлениями.", "horizon.rep@talenthub.by", "Ирина Соколова"),
    MockOrganization("Гимназия «Вектор»", OrganizationType.INSTITUTION, "Гимназия с углублённым изучением математики и иностранных языков.", "vector.rep@talenthub.by", "Павел Левченко"),
    MockOrganization("НоваЛаб", OrganizationType.COMPANY, "Технологическая компания: разработка, анализ данных и инженерные практикумы.", "novalab.rep@talenthub.by", "Елена Романова"),
    MockOrganization("КодПульс", OrganizationType.COMPANY, "Команда разработчиков образовательных сервисов и профориентационных программ.", "codepulse.rep@talenthub.by", "Максим Белый"),
    MockOrganization("Академия «ПрофСтарт»", OrganizationType.ACADEMY, "Короткие программы знакомства с современными профессиями.", "profstart.rep@talenthub.by", "Ольга Климова"),
    MockOrganization("Школа технологий «Орбита»", OrganizationType.ACADEMY, "Проектное обучение робототехнике и цифровому дизайну.", "orbita.rep@talenthub.by", "Денис Волков"),
)

MOCK_STUDENTS = tuple(SeedUser(email, name, UserRole.STUDENT) for email, name in (
    ("mock.student01@talenthub.by", "София Новик"), ("mock.student02@talenthub.by", "Артём Лис"),
    ("mock.student03@talenthub.by", "Виктория Мельник"), ("mock.student04@talenthub.by", "Никита Зорин"),
    ("mock.student05@talenthub.by", "Полина Светлова"), ("mock.student06@talenthub.by", "Даниил Марков"),
    ("mock.student07@talenthub.by", "Алина Берест"), ("mock.student08@talenthub.by", "Кирилл Янов"),
))

PRIMARY_DEMO_STUDENT = SeedUser("student@talenthub.by", "Анна Коваль", UserRole.STUDENT)

CATEGORIES = (("programming", "Программирование"), ("science", "Наука"), ("engineering", "Инженерия"), ("robotics", "Робототехника"), ("design", "Дизайн"), ("business", "Предпринимательство"), ("media", "Медиа"), ("languages", "Языки"), ("career", "Профориентация"))
EVENT_TEMPLATES = (
    ("python-lab", "Python: от идеи до прототипа", "programming", 5, EventFormat.OFFLINE, "1515879218367-8466d910aaa4"),
    ("robotics-cup", "Кубок школьной робототехники", "robotics", 10, EventFormat.OFFLINE, "1485827404703-89b55fcc595e"),
    ("data-weekend", "Data Weekend для начинающих", "science", 14, EventFormat.HYBRID, "1551288049-bebda4e38f71"),
    ("design-city", "Дизайн городской среды", "design", 18, EventFormat.OFFLINE, "1497366754035-f200968a6e72"),
    ("startup-school", "Школа юного предпринимателя", "business", 22, EventFormat.HYBRID, "1556761175-b413da4baf72"),
    ("media-story", "Медиалаборатория: рассказывать историями", "media", 26, EventFormat.ONLINE, "1485846234645-a62644f84728"),
    ("english-debate", "English Debate Club", "languages", 30, EventFormat.OFFLINE, "1524178232363-1fb2b075b655"),
    ("career-tech", "Как выбрать профессию в технологиях", "career", 34, EventFormat.ONLINE, "1521737711867-e3b97375f902"),
    ("physics-experiment", "Физика живого эксперимента", "science", 38, EventFormat.OFFLINE, "1532094349884-543bc11b234d"),
    ("web-intensive", "Веб-интенсив: первая страница", "programming", 42, EventFormat.HYBRID, "1498050108023-c5249f4df085"),
    ("drone-engineering", "Инженерия беспилотников", "engineering", 46, EventFormat.OFFLINE, "1508614999368-9260051292e5"),
    ("product-design", "Продуктовый дизайн без магии", "design", 50, EventFormat.ONLINE, "1561070791-2526d30994b5"),
    ("bio-research", "Биология: настоящее исследование", "science", 54, EventFormat.OFFLINE, "1532187863486-abf9dbad1b69"),
    ("game-dev", "Создаём игру за выходные", "programming", 58, EventFormat.HYBRID, "1550745165-9bc0b252726f"),
    ("future-campus", "Кампус будущего", "engineering", 62, EventFormat.OFFLINE, "1503387762-592deb58ef4e"),
    ("career-meetup", "Встреча с инженерами и разработчиками", "career", 66, EventFormat.HYBRID, "1517245386807-bb43f82c33c4"),
    ("social-project", "Проект, который меняет город", "business", 70, EventFormat.OFFLINE, "1529390079861-591de354faf5"),
    ("motion-lab", "Motion-дизайн: движение и смысл", "design", 74, EventFormat.ONLINE, "1558655146-d09347e92766"),
    ("archive-hackathon", "Осенний образовательный хакатон", "programming", -25, EventFormat.OFFLINE, "1504384308090-c894fdcc538d"),
    ("archive-science", "Научный фестиваль лицеев", "science", -50, EventFormat.OFFLINE, "1509062522246-3755977927d7"),
)

EVENT_DESCRIPTIONS = {
    "python-lab": "За один день участники соберут рабочий Python-прототип: разберут задачу, напишут код и представят результат экспертам.",
    "robotics-cup": "Командные соревнования роботов: сборка, настройка датчиков, программирование движения и финальный заезд на полигоне.",
    "data-weekend": "Практикум по данным с понятными задачами из реального мира: от очистки таблицы до наглядного вывода и презентации.",
    "design-city": "Исследуем городскую среду, замечаем проблемы маршрутов и общественных пространств, затем создаём собственную концепцию улучшения.",
    "startup-school": "Участники пройдут путь от проблемы и целевой аудитории до ценностного предложения и короткого питча проекта.",
    "media-story": "Учимся находить героя, выстраивать драматургию и собирать короткую цифровую историю из текста, фото и звука.",
    "english-debate": "Дебаты на английском языке с подготовкой аргументов, работой в командах и обратной связью от преподавателей.",
    "career-tech": "Разговор с практиками о разработке, аналитике, дизайне и инженерии — без рекламных обещаний и с реальными маршрутами входа.",
    "physics-experiment": "Лабораторный день с измерениями, гипотезами и экспериментами, результаты которых участники оформят как мини-исследование.",
    "web-intensive": "Собираем адаптивную веб-страницу с нуля и разбираемся, как связаны структура, визуальный стиль и поведение интерфейса.",
    "drone-engineering": "Знакомство с устройством беспилотников, принципами управления и безопасным тестированием инженерных решений.",
    "product-design": "Разбираем пользовательскую задачу, строим сценарий и создаём прототип продукта, который можно проверить на людях.",
    "bio-research": "От наблюдения и исследовательского вопроса до аккуратного эксперимента, фиксации данных и защиты вывода.",
    "game-dev": "Команды придумают механику, соберут небольшую игру и проведут взаимное тестирование прототипов.",
    "future-campus": "Проектная сессия о пространствах для учёбы: свет, акустика, навигация, совместная работа и цифровая инфраструктура.",
    "career-meetup": "Неформальные встречи с инженерами и разработчиками: рабочие задачи, образование, ошибки и первые проекты для портфолио.",
    "social-project": "Находим локальную проблему, изучаем заинтересованные стороны и проектируем небольшой, но измеримый городской проект.",
    "motion-lab": "Практика композиции и движения: участники соберут короткую анимацию и получат разбор визуального ритма.",
    "archive-hackathon": "Командный хакатон, на котором учащиеся создали работающие прототипы образовательных сервисов и защитили их перед жюри.",
    "archive-science": "Фестиваль школьных исследований с демонстрациями, постерными докладами и экспертной обратной связью.",
}


def seed_mock_data(password: str | None = None) -> tuple[int, int]:
    settings = get_settings()
    mock_password = password or settings.mock_data_password
    if mock_password is None or len(mock_password) < 8:
        raise RuntimeError("Set MOCK_DATA_PASSWORD to at least 8 characters before seeding mock data")
    primary_password = settings.demo_student_password
    if primary_password is None or len(primary_password) < 8:
        primary_password = mock_password
    created_organizations = created_users = 0
    now = datetime.now(UTC).replace(microsecond=0)
    with SessionLocal.begin() as session:
        organizations: list[Organization] = []
        created_student_emails: set[str] = set()
        for index, source in enumerate(MOCK_ORGANIZATIONS):
            organization, created = get_or_create_organization(session, source.name, source.type, source.description)
            created_organizations += int(created); organizations.append(organization)
            if created:
                organization.region = "Минск" if index != 1 else "Гомель"; organization.directions = "образование, проекты, профориентация"; organization.contact_email = source.representative_email
            role = UserRole.INSTITUTION_REPRESENTATIVE if source.type == OrganizationType.INSTITUTION else UserRole.ORGANIZATION_REPRESENTATIVE
            created_users += int(create_user_if_missing(session, SeedUser(source.representative_email, source.representative_name, role), mock_password, organization))
        primary_created = create_user_if_missing(session, PRIMARY_DEMO_STUDENT, primary_password)
        created_users += int(primary_created)
        if primary_created:
            created_student_emails.add(PRIMARY_DEMO_STUDENT.email)
        for student in MOCK_STUDENTS:
            created = create_user_if_missing(session, student, mock_password)
            created_users += int(created)
            if created:
                created_student_emails.add(student.email)
        session.flush()

        categories: dict[str, Category] = {}
        for slug, name in CATEGORIES:
            item = session.scalar(select(Category).where(Category.slug == slug))
            if item is None:
                item = Category(slug=slug, name=name); session.add(item); session.flush()
            categories[slug] = item

        all_student_emails = [PRIMARY_DEMO_STUDENT.email, *[item.email for item in MOCK_STUDENTS]]
        students = list(session.scalars(select(User).options(selectinload(User.student_profile).selectinload(StudentProfile.interests)).where(User.email.in_(all_student_emails))).all())
        for index, student in enumerate(students):
            profile_created = student.student_profile is None
            if student.student_profile is None:
                student.student_profile = StudentProfile(grade=7 + index % 5, region=("Минск", "Гомель", "Брест")[index % 3])
            elif student.email in created_student_emails:
                student.student_profile.grade = 7 + index % 5
                student.student_profile.region = ("Минск", "Гомель", "Брест")[index % 3]
            if not student.student_profile.bio:
                student.student_profile.bio = "Интересуюсь образовательными проектами и хочу собрать сильное портфолио практических работ."
            if not student.student_profile.interests:
                interest_slugs = (
                    ("programming", "science", "engineering", "career")
                    if student.email == PRIMARY_DEMO_STUDENT.email
                    else ("design", "media", "languages", "career")
                    if student.email == MOCK_STUDENTS[0].email
                    else (CATEGORIES[index % 9][0], CATEGORIES[(index + 2) % 9][0])
                )
                student.student_profile.interests = [categories[slug] for slug in interest_slugs]

        events: dict[str, Event] = {}
        old_mock_photos = ("1516321318423-f06f85e504b3", "1532094349884-543bc11b234d", "1509062522246-3755977927d7", "1517245386807-bb43f82c33c4")
        for index, (slug, title, category_slug, day_offset, event_format, photo_id) in enumerate(EVENT_TEMPLATES):
            event = session.scalar(select(Event).where(Event.slug == slug))
            if event is None:
                start = now + timedelta(days=day_offset, hours=10)
                event = Event(slug=slug, organizer=organizations[index % len(organizations)], title=title, summary=EVENT_DESCRIPTIONS[slug].split(".")[0] + ".", description=EVENT_DESCRIPTIONS[slug], image_url=f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=1400&q=80", starts_at=start, ends_at=start + timedelta(hours=3), registration_deadline=start - timedelta(days=2), format=event_format, region=("Минск", "Гомель", "Брест")[index % 3], venue=None if event_format == EventFormat.ONLINE else organizations[index % len(organizations)].name, address=None if event_format == EventFormat.ONLINE else "образовательная площадка, центральный корпус", meeting_url="https://meet.example.org/talenthub" if event_format != EventFormat.OFFLINE else None, target_audience="Учащиеся 7–11 классов", min_grade=7, max_grade=11, participation_terms="Участие бесплатное, нужна предварительная регистрация.", capacity=20 + index * 2, requires_approval=index % 3 == 0, status=EventStatus.PUBLISHED if index not in {3, 11} else EventStatus.DRAFT, categories=[categories[category_slug]])
                session.add(event); session.flush()
            else:
                if event.description == f"Участники познакомятся с темой «{title}», поработают в командах и создадут собственный результат. Программа рассчитана на учащихся 7–11 классов.":
                    event.summary = EVENT_DESCRIPTIONS[slug].split(".")[0] + "."
                    event.description = EVENT_DESCRIPTIONS[slug]
                if event.image_url and any(photo in event.image_url for photo in old_mock_photos):
                    event.image_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=1400&q=80"
            events[slug] = event

        featured_scenarios = {
            PRIMARY_DEMO_STUDENT.email: (
                ("python-lab", RegistrationStatus.PENDING),
                ("robotics-cup", RegistrationStatus.APPROVED),
                ("data-weekend", RegistrationStatus.REJECTED),
                ("startup-school", RegistrationStatus.CANCELLED),
                ("archive-hackathon", RegistrationStatus.ATTENDED),
            ),
            MOCK_STUDENTS[0].email: (
                ("english-debate", RegistrationStatus.PENDING),
                ("media-story", RegistrationStatus.APPROVED),
                ("career-tech", RegistrationStatus.REJECTED),
                ("physics-experiment", RegistrationStatus.CANCELLED),
                ("archive-science", RegistrationStatus.ATTENDED),
            ),
        }

        def ensure_registration(student: User, event_slug: str, registration_status: RegistrationStatus) -> None:
            event = events[event_slug]
            registration = session.scalar(select(EventRegistration).where(EventRegistration.event_id == event.id, EventRegistration.student_id == student.id))
            if registration is None:
                registration = EventRegistration(event=event, student=student, status=registration_status)
                session.add(registration)
                session.flush()
            if registration.status == RegistrationStatus.ATTENDED and registration.achievement is None:
                session.add(Achievement(student=student, registration=registration, title=event.title, description=f"Подтверждённое участие в событии «{event.title}»."))

        statuses = (RegistrationStatus.PENDING, RegistrationStatus.APPROVED, RegistrationStatus.REJECTED, RegistrationStatus.CANCELLED, RegistrationStatus.ATTENDED)
        regular_students = [student for student in students if student.email not in featured_scenarios]
        for index, student in enumerate(regular_students):
            ensure_registration(student, list(events)[index % 8], statuses[index % len(statuses)])
        for student in students:
            for event_slug, registration_status in featured_scenarios.get(student.email, ()):
                ensure_registration(student, event_slug, registration_status)

        for title, creator, target, direction in (
            ("Лаборатория инженерных проектов", organizations[0], None, OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION),
            ("Карьерный день для старшеклассников", organizations[2], None, OpportunityDirection.ORGANIZATION_SEEKS_INSTITUTION),
            ("Совместный курс по робототехнике", organizations[1], organizations[5], OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION),
        ):
            if session.scalar(select(PartnershipOpportunity).where(PartnershipOpportunity.title == title, PartnershipOpportunity.creator_organization_id == creator.id)) is None:
                session.add(PartnershipOpportunity(creator_organization=creator, target_organization=target, direction=direction, title=title, description=f"Ищем партнёра для инициативы «{title}» с понятным вкладом обеих сторон.", topic="образовательные проекты", format="очно и онлайн", target_audience="учащиеся 8–11 классов", conditions="Совместно согласовать программу и экспертов.", desired_start=date.today() + timedelta(days=30), desired_end=date.today() + timedelta(days=90)))
        session.flush()

        if session.scalar(select(PartnershipOpportunity).where(PartnershipOpportunity.title == "Завершённая инженерная мастерская")) is None:
            opportunity = PartnershipOpportunity(creator_organization=organizations[0], target_organization=organizations[2], direction=OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION, title="Завершённая инженерная мастерская", description="Совместная серия инженерных занятий для лицеистов.", topic="инженерия", format="очно", target_audience="9–11 классы", conditions="Эксперты компании и площадка лицея.", status=OpportunityStatus.CLOSED)
            response = PartnershipResponse(opportunity=opportunity, responder_organization=organizations[2], message="Готовы предоставить экспертов и оборудование.", status=ResponseStatus.ACCEPTED)
            partnership = Partnership(opportunity=opportunity, accepted_response=response, organization_a=organizations[0], organization_b=organizations[2], organization_a_confirmed=True, organization_b_confirmed=True, status=PartnershipStatus.COMPLETED, completed_at=now - timedelta(days=10))
            session.add(partnership); session.flush()
            for organization in (organizations[0], organizations[2]):
                session.add(PrestigeEntry(organization=organization, partnership=partnership, points=PRESTIGE_POINTS_PER_PARTNERSHIP, reason="Подтверждённая совместная инициатива «Завершённая инженерная мастерская»"))

    print(f"Mock seed complete. Created {created_organizations} organization(s) and {created_users} user(s); product data is ready and existing records were preserved.")
    return created_organizations, created_users


if __name__ == "__main__":
    seed_mock_data()
