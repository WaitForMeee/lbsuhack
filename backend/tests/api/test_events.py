from datetime import timedelta

from app.db.session import SessionLocal
from app.models import Event
from app.scripts.seed_demo import demo_id
from app.services.shared.time import today

API = "/api/v1"


def payload(**updates):
    return dict(
        title="Новое мероприятие",
        description="Проверяем цепочку API",
        kind="project",
        project_kind="hackathon",
        interests=["Информатика"],
        grade_min=10,
        grade_max=11,
        event_date=(today() + timedelta(days=7)).isoformat(),
        registration_deadline=today().isoformat(),
        city="Минск",
        venue="КодМастер",
        format="offline",
        terms="Бесплатно",
        capacity=1,
        **updates,
    )


def event_id(name):
    return str(demo_id("event:" + name))


def test_event_end_to_end(client, auth):
    created = client.post(API + "/events", headers=auth("company"), json=payload())
    assert created.status_code == 201, created.text
    e = created.json()
    path = API + "/events/" + e["id"]
    assert e["status"] == "pending"
    assert client.get(path).status_code == 404
    assert client.get(path, headers=auth("school")).status_code == 404
    queue = client.get(API + "/moderation/queue", headers=auth("admin")).json()
    assert any(r["id"] == e["id"] for r in queue["events"]["items"])
    review = API + "/moderation/events/" + e["id"] + "/decision"
    assert (
        client.post(
            review, headers=auth("admin"), json={"decision": "approve"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            review, headers=auth("admin"), json={"decision": "approve"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            review, headers=auth("admin"), json={"decision": "reject"}
        ).status_code
        == 409
    )
    assert client.get(path).status_code == 200
    feed = client.get(API + "/notifications/me", headers=auth("alina")).json()["items"]
    assert len([n for n in feed if n["event_id"] == e["id"]]) == 1
    # Deadline is inclusive in Minsk, and grades are audience labels, not a restriction.
    assert client.post(path + "/registrations", headers=auth("mark")).status_code == 409
    school = str(demo_id("org:school"))
    client.patch(
        API + "/students/me",
        headers=auth("mark"),
        json=dict(grade=7, city="Минск", interests=["Математика"], school_id=school),
    )
    registered = client.post(path + "/registrations", headers=auth("mark"))
    assert registered.status_code == 201, registered.text
    r = registered.json()
    reg_path = API + "/registrations/" + r["id"]
    assert client.post(path + "/registrations", headers=auth("mark")).status_code == 200
    assert (
        client.patch(
            reg_path + "/decision",
            headers=auth("school"),
            json={"decision": "approved"},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            reg_path + "/decision",
            headers=auth("company"),
            json={"decision": "approved"},
        ).status_code
        == 200
    )
    other = client.post(path + "/registrations", headers=auth("alina")).json()
    assert (
        client.patch(
            API + "/registrations/" + other["id"] + "/decision",
            headers=auth("company"),
            json={"decision": "approved"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            reg_path + "/decision",
            headers=auth("company"),
            json={"decision": "approved"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            reg_path + "/decision",
            headers=auth("company"),
            json={"decision": "rejected"},
        ).status_code
        == 409
    )
    attendance = client.put(reg_path + "/attendance", headers=auth("company")).json()[
        "attended_at"
    ]
    assert (
        client.put(reg_path + "/attendance", headers=auth("company")).json()[
            "attended_at"
        ]
        == attendance
    )
    assert client.post(reg_path + "/cancel", headers=auth("mark")).status_code == 409
    success = client.get(API + "/students/me/success", headers=auth("mark")).json()
    assert len(success["attendances"]) == 1 and success["achievements"] == []
    assert client.post(path + "/complete", headers=auth("company")).status_code == 200
    assert (
        client.post(review, headers=auth("admin"), json={"decision": "approve"}).json()[
            "status"
        ]
        == "completed"
    )
    assert client.get(path).status_code == 404
    assert client.get(path, headers=auth("mark")).status_code == 200


def test_cancel_reactivate_close_and_deadline(client, auth):
    path = API + "/events/" + event_id("junior")
    r = client.post(path + "/registrations", headers=auth("alina")).json()
    reg_path = API + "/registrations/" + r["id"]
    assert client.post(reg_path + "/cancel", headers=auth("mark")).status_code == 404
    assert client.post(reg_path + "/cancel", headers=auth("alina")).status_code == 200
    assert client.post(reg_path + "/cancel", headers=auth("alina")).status_code == 200
    cancelled = client.get(
        API + "/events?application_status=cancelled", headers=auth("alina")
    ).json()["items"]
    assert any(e["id"] == event_id("junior") for e in cancelled)
    none = client.get(
        API + "/events?application_status=none", headers=auth("alina")
    ).json()["items"]
    assert not any(e["id"] == event_id("junior") for e in none)
    reapplied = client.post(path + "/registrations", headers=auth("alina"))
    assert reapplied.status_code == 201 and reapplied.json()["id"] == r["id"]
    assert (
        client.post(path + "/close-registration", headers=auth("school")).status_code
        == 404
    )
    assert (
        client.post(path + "/close-registration", headers=auth("company")).status_code
        == 200
    )
    assert (
        client.post(path + "/registrations", headers=auth("alina")).status_code == 200
    )
    assert client.post(path + "/registrations", headers=auth("ilya")).status_code == 404
    assert (
        client.post(path + "/open-registration", headers=auth("company")).status_code
        == 200
    )
    with SessionLocal.begin() as db:
        db.get(Event, demo_id("event:junior")).registration_deadline = (
            today() - timedelta(days=1)
        )
    assert client.post(path + "/registrations", headers=auth("ilya")).status_code == 409
    assert (
        client.post(path + "/close-registration", headers=auth("company")).status_code
        == 200
    )
    assert (
        client.post(path + "/open-registration", headers=auth("company")).status_code
        == 409
    )


def test_catalog_recommendations_and_prepared_states(client, auth):
    for q in ("КодМастер", "Минск", "лаборатория", "Бесплатно"):
        assert client.get(API + "/events", params={"q": q}).json()["items"]
    items = client.get(
        API + "/events", params=[("interest", "Биология"), ("interest", "Математика")]
    ).json()["items"]
    assert items and all(
        set(e["interests"]) & {"Биология", "Математика"} for e in items
    )
    assert client.get(API + "/events?application_status=none").status_code == 401
    assert (
        client.get(
            API + "/events?application_status=none", headers=auth("company")
        ).status_code
        == 403
    )
    assert client.get(API + "/recommendations", headers=auth("mark")).json() == {
        "items": []
    }
    recommendations = client.get(
        API + "/recommendations?interest=Биология", headers=auth("alina")
    ).json()["items"]
    assert recommendations and all(
        "Биология" in e["interests"] for e in recommendations
    )
    assert len(recommendations) <= 3
    for status, key, organizer in [
        ("under_review", "review", "company"),
        ("waitlisted", "wait", "school"),
    ]:
        found = client.get(
            API + "/events?application_status=" + status, headers=auth("alina")
        ).json()["items"]
        assert len(found) == 1
        if key in ("wait", "review"):
            identity = str(demo_id("registration:" + key))
            assert (
                client.patch(
                    API + "/registrations/" + identity + "/decision",
                    headers=auth(organizer),
                    json={"decision": "approved"},
                ).status_code
                == 200
            )
    assert (
        client.post(
            API + "/events/" + event_id("chem") + "/registrations",
            headers=auth("alina"),
        ).status_code
        == 409
    )


def test_roster_transfer_does_not_revoke_organizer_access(client, auth):
    client.patch(
        API + "/students/me",
        headers=auth("alina"),
        json={"school_id": str(demo_id("org:school2"))},
    )
    people = client.get(
        API + "/events/" + event_id("math") + "/registrations", headers=auth("school")
    )
    assert people.status_code == 200
    assert any(
        p["student_user_id"] == str(demo_id("user:alina"))
        for p in people.json()["items"]
    )
    assert (
        client.get(
            API + "/events/" + event_id("math") + "/registrations",
            headers=auth("company"),
        ).status_code
        == 404
    )
