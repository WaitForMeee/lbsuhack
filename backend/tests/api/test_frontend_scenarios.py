from app.scripts.seed_demo import demo_id

API = "/api/v1"


def test_parent_multiple_children_switch_recommend_suggest_and_notification_read(
    client, auth
):
    headers = auth("olga")
    initial = client.get(API + "/parents/me/children", headers=headers).json()
    assert len(initial["items"]) == 1
    assert initial["items"][0]["profile"]["id"] == str(demo_id("user:alina"))
    assert initial["active_child_id"] == str(demo_id("user:alina"))
    invitation = client.post(API + "/parents/me/invitation", headers=headers).json()["invitation"]["token"]
    for persona in ("alina", "mark"):
        r = client.post(API + "/family-invitations/accept", headers=auth(persona), json={"token": invitation})
        assert r.status_code == 200, r.text
    children = client.get(API + "/parents/me/children", headers=headers).json()
    assert len(children["items"]) == 2
    alina = str(demo_id("user:alina"))
    assert (
        client.put(
            API + f"/parents/me/children/{alina}/select", headers=headers
        ).json()["child"]["profile"]["id"]
        == alina
    )
    assert (
        client.get(API + "/parents/me/child", headers=headers).json()["child"][
            "profile"
        ]["id"]
        == alina
    )
    assert (
        client.get(
            API + f"/parents/me/children/{alina}/recommendations", headers=headers
        ).status_code
        == 200
    )
    stranger = str(demo_id("user:ilya"))
    assert (
        client.put(
            API + f"/parents/me/children/{stranger}/select", headers=headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            API + f"/parents/me/children/{stranger}/recommendations", headers=headers
        ).status_code
        == 404
    )
    event = str(demo_id("event:junior"))
    path = API + f"/parents/me/children/{alina}/suggestions"
    one = client.post(path, headers=headers, json={"event_id": event})
    two = client.post(path, headers=headers, json={"event_id": event})
    assert one.status_code == 201 and one.json()["id"] == two.json()["id"]
    assert (
        len(
            client.get(API + "/parents/me/suggestions", headers=headers).json()["items"]
        )
        == 1
    )
    feed = client.get(API + "/notifications/me", headers=auth("alina")).json()
    invites = [
        n for n in feed["items"] if n["title"] == "Родитель предлагает мероприятие"
    ]
    assert len(invites) == 1
    notification = invites[0]["id"]
    assert (
        client.put(
            API + f"/notifications/{notification}/read", headers=auth("mark")
        ).status_code
        == 404
    )
    for _ in range(2):
        result = client.put(
            API + f"/notifications/{notification}/read", headers=auth("alina")
        )
        assert result.status_code == 200 and result.json()["read"] is True


def test_public_school_offer_is_moderated_and_company_responses_are_independent(
    client, auth
):
    created = client.post(
        API + "/partnership-requests",
        headers=auth("writer-school"),
        json=dict(
            visibility="all_companies",
            title="Нужны наставники",
            description="Ищем наставников для проектной смены.",
        ),
    )
    assert created.status_code == 201, created.text
    identity = created.json()["id"]
    market = lambda: client.get(
        API + "/partnership-requests?view=marketplace", headers=auth("writer-company")
    ).json()["items"]
    assert all(p["id"] != identity for p in market())
    assert (
        client.post(
            API + f"/moderation/partnership-requests/{identity}/decision",
            headers=auth("writer-admin"),
            json={"decision": "approve"},
        ).status_code
        == 200
    )
    assert any(p["id"] == identity for p in market())
    for persona in ("company", "academy"):
        row = client.post(
            API + f"/partnership-requests/{identity}/responses", headers=auth("writer-" + persona)
        )
        assert row.status_code == 201, row.text
        assert row.json()["organization"]["kind"] in ("company", "academy")
        assert row.json()["school"] is None
        response_id = row.json()["id"]
        assert (
            client.patch(
                API + f"/partnership-responses/{response_id}/decision",
                headers=auth("writer-school2"),
                json={"decision": "accepted"},
            ).status_code
            == 404
        )
        assert (
            client.patch(
                API + f"/partnership-responses/{response_id}/decision",
                headers=auth("writer-school"),
                json={"decision": "accepted"},
            ).status_code
            == 200
        )
    assert (
        client.post(
            API + f"/partnership-requests/{identity}/responses", headers=auth("writer-school2")
        ).status_code
        == 404
    )


def test_school_directory_counts_only_confirmed_achievements_by_event(client, auth):
    def directory():
        return client.get(API + "/schools").json()["items"]

    school = lambda: next(
        s for s in directory() if s["id"] == str(demo_id("org:school"))
    )
    assert sum(i["count"] for i in school()["indicators"]) == 1
    # A new attendance alone must not turn into an achievement or inflate the ranking.
    registration = str(demo_id("registration:math"))
    client.put(
        API + f"/registrations/{registration}/attendance", headers=auth("writer-school")
    )
    assert sum(i["count"] for i in school()["indicators"]) == 1
    assert all("first_name" not in str(row) for row in directory())
    roster = client.get(
        API + "/organizations/me/students", headers=auth("writer-school")
    ).json()["items"]
    student = next(s for s in roster if s["id"] == str(demo_id("user:alina")))
    assert student["application_count"] == len(student["applications"])
    assert student["attendance_count"] == len(student["attendances"])
