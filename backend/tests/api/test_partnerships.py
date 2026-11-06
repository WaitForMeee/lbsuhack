from app.scripts.seed_demo import demo_id

API = "/api/v1"


def test_direct_moderation_visibility_and_retries(client, auth):
    school_id = str(demo_id("org:school2"))
    response = client.post(
        API + "/partnership-requests",
        headers=auth("company"),
        json=dict(
            visibility="direct",
            target_org_id=school_id,
            title="Новый запрос",
            description="Образовательная программа",
        ),
    )
    assert response.status_code == 201, response.text
    identity = response.json()["id"]
    path = API + "/partnership-requests/" + identity
    listing = lambda persona: client.get(
        API + "/partnership-requests", headers=auth(persona)
    ).json()["items"]
    assert not any(p["id"] == identity for p in listing("school2"))
    assert (
        client.patch(
            path + "/decision", headers=auth("school2"), json={"decision": "accepted"}
        ).status_code
        == 404
    )
    review = API + "/moderation/partnership-requests/" + identity + "/decision"
    assert (
        client.post(
            review, headers=auth("admin"), json={"decision": "approve"}
        ).status_code
        == 200
    )
    assert any(p["id"] == identity for p in listing("school2"))
    assert (
        client.patch(
            path + "/decision", headers=auth("school"), json={"decision": "accepted"}
        ).status_code
        == 404
    )
    for _ in range(2):
        r = client.patch(
            path + "/decision", headers=auth("school2"), json={"decision": "accepted"}
        )
        assert r.status_code == 200 and r.json()["direct_decision"] == "accepted"
    assert (
        client.patch(
            path + "/decision", headers=auth("school2"), json={"decision": "declined"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            review, headers=auth("admin"), json={"decision": "reject"}
        ).status_code
        == 409
    )


def test_two_school_responses_and_visibility(client, auth):
    path = API + "/partnership-requests/" + str(demo_id("partnership:market"))
    responses = []
    for school in ("school", "school2"):
        r = client.post(path + "/responses", headers=auth(school))
        assert r.status_code == 201, r.text
        responses.append(r.json())
        assert (
            client.post(path + "/responses", headers=auth(school)).json()["id"]
            == r.json()["id"]
        )
    for response in responses:
        route = API + "/partnership-responses/" + response["id"] + "/decision"
        assert (
            client.patch(
                route, headers=auth("academy"), json={"decision": "accepted"}
            ).status_code
            == 404
        )
        assert (
            client.patch(
                route, headers=auth("company"), json={"decision": "accepted"}
            ).status_code
            == 200
        )
        assert (
            client.patch(
                route, headers=auth("company"), json={"decision": "accepted"}
            ).status_code
            == 200
        )
        assert (
            client.patch(
                route, headers=auth("company"), json={"decision": "declined"}
            ).status_code
            == 409
        )
    for persona, count in [("school", 1), ("school2", 1), ("company", 2)]:
        item = next(
            p
            for p in client.get(
                API + "/partnership-requests", headers=auth(persona)
            ).json()["items"]
            if p["id"] == str(demo_id("partnership:market"))
        )
        assert len(item["responses"]) == count
    assert (
        client.get(
            API + "/partnership-requests?view=marketplace", headers=auth("company")
        ).status_code
        == 403
    )
    assert client.post(path + "/responses", headers=auth("company")).status_code == 403


def test_invalid_partnership_directions(client, auth):
    base = dict(title="Предложение", description="Описание")
    for persona, fields in [
        ("school", dict(visibility="all_schools")),
        (
            "company",
            dict(visibility="direct", target_org_id=str(demo_id("org:academy"))),
        ),
        (
            "school",
            dict(visibility="direct", target_org_id=str(demo_id("org:school2"))),
        ),
        ("company", dict(visibility="direct")),
        (
            "company",
            dict(visibility="all_schools", target_org_id=str(demo_id("org:school"))),
        ),
    ]:
        assert (
            client.post(
                API + "/partnership-requests",
                headers=auth(persona),
                json={**base, **fields},
            ).status_code
            == 422
        )
    assert (
        client.post(
            API + "/partnership-requests",
            headers=auth("school"),
            json={
                **base,
                "visibility": "direct",
                "target_org_id": str(demo_id("org:academy")),
            },
        ).status_code
        == 201
    )


def test_queue_achievement_counters_and_access(client, auth):
    queue = client.get(API + "/moderation/queue", headers=auth("admin")).json()
    assert all(
        queue[key]["items"]
        for key in ("events", "partnership_requests", "achievements")
    )
    assert (
        client.get(API + "/moderation/queue", headers=auth("company")).status_code
        == 403
    )
    achievement = queue["achievements"]["items"][0]
    path = API + "/moderation/achievements/" + achievement["id"] + "/decision"
    for _ in range(2):
        assert (
            client.post(
                path, headers=auth("admin"), json={"decision": "approve"}
            ).status_code
            == 200
        )
    after = client.get(API + "/moderation/queue", headers=auth("admin")).json()
    assert (
        after["achievements"]["decided_count"]
        == queue["achievements"]["decided_count"] + 1
    )
    assert (
        len(
            client.get(API + "/students/me/success", headers=auth("alina")).json()[
                "achievements"
            ]
        )
        == 2
    )
    assert (
        client.post(
            path, headers=auth("admin"), json={"decision": "reject"}
        ).status_code
        == 409
    )
    client.post(
        API + "/events/" + str(demo_id("event:math")) + "/close-registration",
        headers=auth("school"),
    )
    final = client.get(API + "/moderation/queue", headers=auth("admin")).json()
    assert final["events"]["decided_count"] == queue["events"]["decided_count"]
    for persona in ("school", "company"):
        r = client.get(API + "/organizations/me/dashboard", headers=auth(persona))
        assert r.status_code == 200, r.text
        assert r.json()["counters"]["registrations"] > 0
