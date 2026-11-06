from datetime import date

from app.db.session import SessionLocal
from app.models import StudentProfile, User
from app.scripts.seed_demo import demo_id

API = "/api/v1"


def test_onboarding_custom_interests_and_school_transfer(client, auth):
    headers = auth("mark")
    assert (
        client.get(API + "/auth/me", headers=headers).json()["profile_complete"]
        is False
    )
    schools = client.get(API + "/organizations?kind=school").json()["items"]
    school = next(o for o in schools if o["name"] == "Лицей БГУ")
    r = client.patch(
        API + "/students/me",
        headers=headers,
        json=dict(
            school_id=school["id"],
            grade=9,
            city="Минск",
            interests=["  Экология  ", "экология", "3D моделирование"],
        ),
    )
    assert r.status_code == 200, r.text
    assert r.json()["profile_complete"] is True
    assert len(r.json()["interests"]) == 2
    assert (
        client.get(API + "/auth/me", headers=headers).json()["profile_complete"] is True
    )
    assert any(
        s["id"] == r.json()["id"]
        for s in client.get(
            API + "/organizations/me/students", headers=auth("school")
        ).json()["items"]
    )
    assert not any(
        s["id"] == r.json()["id"]
        for s in client.get(
            API + "/organizations/me/students", headers=auth("school2")
        ).json()["items"]
    )
    assert "3D моделирование" not in [
        i["name"] for i in client.get(API + "/reference-data").json()["interests"]
    ]
    assert (
        client.patch(
            API + "/students/me", headers=headers, json={"grade": 6}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            API + "/students/me", headers=headers, json={"grade": None}
        ).status_code
        == 422
    )
    assert client.get(API + "/students/me").status_code == 401
    assert (
        client.get(
            API + "/organizations/me/students", headers=auth("company")
        ).status_code
        == 403
    )
    assert (
        client.get(
            API + "/organizations/me/students",
            headers=auth("school"),
            params={"q": "Марк"},
        ).json()["items"][0]["id"]
        == r.json()["id"]
    )
    client.patch(API + "/students/me", headers=headers, json={"interests": []})
    assert not client.get(API + "/students/me", headers=headers).json()[
        "profile_complete"
    ]


def test_parent_link_privacy_and_failed_replacement(client, auth):
    headers = auth("olga")
    assert client.get(API + "/parents/me/child", headers=headers).json() == {
        "child": None
    }
    match = dict(first_name=" АЛИНА ", last_name="коваль", birth_date="2010-04-12")
    response = client.put(API + "/parents/me/child", headers=headers, json=match)
    assert response.status_code == 200, response.text
    child = response.json()["child"]
    assert "email" not in str(child) and "password" not in str(child)
    assert len(child["attendances"]) == 1 and len(child["achievements"]) == 1
    assert (
        client.put(
            API + "/parents/me/child",
            headers=headers,
            json={**match, "last_name": "Нет"},
        ).status_code
        == 404
    )
    assert (
        client.get(API + "/parents/me/child", headers=headers).json()["child"][
            "profile"
        ]["id"]
        == child["profile"]["id"]
    )
    with SessionLocal.begin() as db:
        u = User(
            email="duplicate@example.org",
            first_name="Алина",
            last_name="Коваль",
            role="student",
            password_hash="unused",
        )
        db.add(u)
        db.flush()
        db.add(
            StudentProfile(
                user_id=u.id,
                birth_date=date(2010, 4, 12),
                school_id=demo_id("org:school"),
            )
        )
    assert (
        client.put(API + "/parents/me/child", headers=headers, json=match).status_code
        == 409
    )
    assert (
        client.get(API + "/parents/me/child", headers=headers).json()["child"][
            "profile"
        ]["id"]
        == child["profile"]["id"]
    )
    assert client.get(API + "/students/me", headers=headers).status_code == 403
