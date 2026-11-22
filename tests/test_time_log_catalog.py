"""platform-empire SPEC-002: a time log's domain reaches the graph as an in-domain set event."""


def set_events(harness, log_id):
    return harness.superuser(
        "SELECT type, payload FROM time.outbox WHERE subject = %s ORDER BY occurred_at",
        (f"empire:time:time-log:{log_id}",),
    )


def test_check_in_domains_map_and_lifecycle_events_flow(client, owner, harness):
    made = client.post(
        "/v1/time-logs",
        headers=owner,
        json={
            "log_date": "2026-11-22",
            "domain": "learning",
            "activity": "Read",
            "minutes": 30,
        },
    )
    assert made.status_code == 201, made.text
    log = made.json()
    events = set_events(harness, log["id"])
    by_type = dict(events)
    assert set(by_type) == {"time.time-log.created", "time.time-log.linked"}
    assert by_type["time.time-log.linked"]["targets"] == [
        "empire:platform:domain:skills"
    ]
    assert by_type["time.time-log.created"]["domain"] == "learning"


def test_unknown_domain_falls_back_to_unclassified(harness):
    [link] = harness.cell.resource("time-log").catalog
    assert link.targets("work") == ["empire:platform:domain:work"]
    assert link.targets("personal") == ["empire:platform:domain:unclassified"]
    assert link.targets("gardening") == ["empire:platform:domain:unclassified"]
