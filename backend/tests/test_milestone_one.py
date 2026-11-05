from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.achievements.achievement import Achievement
from app.models.categories.category import Category
from app.models.prestige.prestige import PrestigeEntry
from app.models.users.user import User


def register_student(client, email="new.student@talenthub.by"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": "student-password", "full_name": "Новый Ученик", "role": "student", "grade": 9, "region": "Минск"})


def register_organization(client, email, name, role="organization_representative", kind="company"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": "organization-password", "full_name": "Представитель", "role": role, "region": "Минск", "organization_name": name, "organization_type": kind, "organization_description": "Организация для образовательных проектов и практических инициатив."})


def test_public_registration_creates_profiles_and_hashes_passwords(client):
    response = register_student(client)
    assert response.status_code == 201
    assert response.json()["role"] == "student"
    assert register_student(client).status_code == 409
    client.post("/api/v1/auth/logout")
    institution = register_organization(client, "school@example.org", "Новая гимназия", "institution_representative", "institution")
    assert institution.status_code == 201
    assert institution.json()["organization"]["type"] == "institution"
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == "new.student@talenthub.by"))
        assert user is not None and user.student_profile is not None
        assert user.password_hash != "student-password"
        assert verify_password("student-password", user.password_hash)


def test_event_registration_attendance_and_portfolio(client):
    organization = register_organization(client, "events@example.org", "Организатор событий")
    organization_id = organization.json()["organization_id"]
    with SessionLocal.begin() as session:
        category = Category(slug="test-tech", name="Тестовая технология")
        session.add(category)
    with SessionLocal() as session:
        category_id = str(session.scalar(select(Category.id).where(Category.slug == "test-tech")))
    start = datetime.now(UTC) + timedelta(days=10)
    payload = {"title": "Практический интенсив", "summary": "Практический интенсив для учащихся старших классов", "description": "Подробная программа практического интенсива с работой в командах и итоговым проектом.", "image_url": None, "starts_at": start.isoformat(), "ends_at": (start + timedelta(hours=3)).isoformat(), "registration_deadline": (start - timedelta(days=1)).isoformat(), "format": "offline", "region": "Минск", "venue": "Лаборатория", "address": "Главный корпус", "meeting_url": None, "target_audience": "Учащиеся 8–11 классов", "min_grade": 8, "max_grade": 11, "participation_terms": "Бесплатно", "capacity": 30, "requires_approval": True, "category_ids": [category_id]}
    created = client.post("/api/v1/events", json=payload)
    assert created.status_code == 201
    event_id = created.json()["id"]
    assert client.post(f"/api/v1/events/{event_id}/publish").status_code == 200
    filtered = client.get("/api/v1/events", params={"search": "Практический", "category": "test-tech", "format": "offline", "region": "Минск"})
    assert filtered.status_code == 200 and filtered.json()["total"] == 1
    client.post("/api/v1/auth/logout")
    student = register_student(client, "flow.student@talenthub.by")
    student_id = student.json()["id"]
    assert client.put("/api/v1/profiles/me/interests", json={"category_ids": [category_id]}).status_code == 200
    recommended = client.get("/api/v1/recommendations")
    assert recommended.status_code == 200 and recommended.json()["items"][0]["id"] == event_id
    assert client.post("/api/v1/events", json=payload).status_code == 403
    registration = client.post(f"/api/v1/events/{event_id}/registrations")
    assert registration.status_code == 201 and registration.json()["status"] == "pending"
    assert client.post(f"/api/v1/events/{event_id}/registrations").status_code == 409
    registration_id = registration.json()["id"]
    client.post("/api/v1/auth/logout")
    assert client.post("/api/v1/auth/login", json={"email": "events@example.org", "password": "organization-password"}).status_code == 200
    assert client.patch(f"/api/v1/registrations/{registration_id}/status", json={"status": "approved"}).status_code == 200
    attended = client.patch(f"/api/v1/registrations/{registration_id}/status", json={"status": "attended"})
    assert attended.status_code == 200
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Achievement).where(Achievement.student_id == UUID(student_id))) == 1
        assert organization_id is not None


def test_partnership_requires_two_confirmations_and_awards_once(client):
    school = register_organization(client, "partner.school@example.org", "Партнёрская школа", "institution_representative", "institution").json()
    school_id = school["organization_id"]
    opportunity = client.post("/api/v1/partnership-opportunities", json={"direction": "institution_seeks_organization", "title": "Инженерная неделя", "description": "Ищем технологического партнёра для совместной инженерной недели в школе.", "topic": "Инженерия", "format": "Очно", "target_audience": "9–11 классы", "conditions": "Совместная программа и эксперты", "desired_start": None, "desired_end": None}).json()
    client.post("/api/v1/auth/logout")
    company = register_organization(client, "partner.company@example.org", "Партнёрская компания").json()
    company_id = company["organization_id"]
    response = client.post(f"/api/v1/partnership-opportunities/{opportunity['id']}/responses", json={"message": "Готовы предоставить экспертов и оборудование."})
    assert response.status_code == 201
    response_id = response.json()["responses"][0]["id"]
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"email": "partner.school@example.org", "password": "organization-password"})
    accepted = client.patch(f"/api/v1/partnership-responses/{response_id}", json={"status": "accepted"})
    assert accepted.status_code == 200
    partnership_id = client.get("/api/v1/partnerships").json()[0]["id"]
    first = client.post(f"/api/v1/partnerships/{partnership_id}/confirm-completion")
    assert first.json()["status"] == "active"
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"email": "partner.company@example.org", "password": "organization-password"})
    second = client.post(f"/api/v1/partnerships/{partnership_id}/confirm-completion")
    assert second.json()["status"] == "completed"
    assert client.post(f"/api/v1/partnerships/{partnership_id}/confirm-completion").status_code == 200
    with SessionLocal() as session:
        entries = session.scalar(select(func.count()).select_from(PrestigeEntry).where(PrestigeEntry.organization_id.in_([UUID(school_id), UUID(company_id)])))
        assert entries == 2
