"""platform-empire SPEC-002: a time log's domain reaches the graph as an in-domain set event."""

from pathlib import Path


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
    # the lifecycle payload carries no raw values: the outbox outlives a deleted log
    assert by_type["time.time-log.created"] == {"version": 1, "deleted": False}


def test_unknown_domain_falls_back_to_unclassified(harness):
    [link] = harness.cell.resource("time-log").catalog
    assert link.targets("work") == ["empire:platform:domain:work"]
    assert link.targets("personal") == ["empire:platform:domain:unclassified"]
    assert link.targets("gardening") == ["empire:platform:domain:unclassified"]


BACKFILL = (
    Path(__file__).resolve().parents[1] / "migrations" / "0002_catalog_backfill.sql"
)


def run_backfill(harness):
    with (
        harness.cluster.connect(harness.cell.role("migrator")) as conn,
        conn.transaction(),
    ):
        conn.execute(BACKFILL.read_text(encoding="utf-8"))


def test_backfill_queues_node_then_domain_set_at_the_row_version(
    client, owner, harness
):
    """Rollout step 4: rows written before the producer get a node event, then their set event."""
    [link] = harness.cell.resource("time-log").catalog
    ids = {}
    for domain in ("work", "learning", "personal", "gardening"):
        made = client.post(
            "/v1/time-logs",
            headers=owner,
            json={"log_date": "2026-11-01", "domain": domain, "activity": "x"},
        )
        assert made.status_code == 201, made.text
        ids[domain] = made.json()["id"]
    edited = client.patch(
        f"/v1/time-logs/{ids['work']}",
        headers=owner,
        json={"minutes": 5},
    )
    assert edited.status_code == 200, edited.text
    # as if written before the producer: nothing queued yet
    harness.superuser(
        "DELETE FROM time.outbox WHERE subject = ANY(%s) RETURNING id",
        ([f"empire:time:time-log:{i}" for i in ids.values()],),
    )
    run_backfill(harness)
    for domain, log_id in ids.items():
        version = 2 if domain == "work" else 1
        events = set_events(harness, log_id)
        assert [t for t, _ in events] == [
            "time.time-log.updated",
            "time.time-log.linked",
        ]
        assert events[0][1] == {"version": version, "deleted": False}
        assert events[1][1] == {
            "relation": "in-domain",
            "mode": "replace",
            "targets": link.targets(domain),
            "set_version": version,
            "version": version,
        }
    # FORCE row level security is back on both tables
    forced = harness.superuser(
        "SELECT relname, relforcerowsecurity FROM pg_class"
        " WHERE oid IN ('time.time_logs'::regclass, 'time.outbox'::regclass)"
    )
    assert all(force for _, force in forced)
