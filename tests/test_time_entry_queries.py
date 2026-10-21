"""Listing, grouping and the lifecycle of a time entry."""

from time_helpers import TIME_ENTRIES, create_entry


def test_list_filters_by_task(client, owner):
    mine = create_entry(client, owner, task_id=9001).json()
    create_entry(client, owner, task_id=9002)
    listed = client.get(TIME_ENTRIES, headers=owner, params={"task_id": 9001})
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()["items"]] == [mine["id"]]


def test_list_filters_by_several_tasks_at_once(client, owner):
    first = create_entry(client, owner, task_id=9101).json()
    second = create_entry(client, owner, task_id=9102).json()
    create_entry(client, owner, task_id=9103)
    listed = client.get(TIME_ENTRIES, headers=owner, params={"task_id": [9101, 9102]})
    assert {item["id"] for item in listed.json()["items"]} == {
        first["id"],
        second["id"],
    }


def test_list_can_ask_for_entries_that_are_still_running(client, owner):
    running = create_entry(client, owner, task_id=9201).json()
    create_entry(
        client,
        owner,
        task_id=9201,
        started_at="2026-01-01T09:00:00+00:00",
        ended_at="2026-01-01T09:30:00+00:00",
    )
    listed = client.get(
        TIME_ENTRIES, headers=owner, params={"task_id": 9201, "null": "ended_at"}
    )
    assert [item["id"] for item in listed.json()["items"]] == [running["id"]]


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(TIME_ENTRIES, headers=owner, params={"source": "manual"})
    assert listed.status_code == 422


def test_list_is_in_creation_order_and_can_be_reversed(client, owner):
    ids = [create_entry(client, owner, task_id=9301).json()["id"] for _ in range(3)]
    ascending = client.get(TIME_ENTRIES, headers=owner, params={"task_id": 9301})
    assert [i["id"] for i in ascending.json()["items"]] == ids
    descending = client.get(
        TIME_ENTRIES, headers=owner, params={"task_id": 9301, "order": "desc"}
    )
    assert [i["id"] for i in descending.json()["items"]] == ids[::-1]


def test_stats_count_entries_per_task(client, owner):
    create_entry(client, owner, task_id=9401)
    create_entry(client, owner, task_id=9401)
    create_entry(client, owner, task_id=9402)
    stats = client.get(
        f"{TIME_ENTRIES}/stats", headers=owner, params={"group_by": "task_id"}
    )
    assert stats.status_code == 200, stats.text
    groups = stats.json()["groups"]
    assert groups["9401"] >= 2
    assert groups["9402"] >= 1


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{TIME_ENTRIES}/stats", headers=owner, params={"group_by": "source"}
    )
    assert stats.status_code == 422


def test_stopping_a_timer_records_the_end_and_duration(client, owner):
    entry = create_entry(client, owner, source="timer").json()
    stopped = client.patch(
        f"{TIME_ENTRIES}/{entry['id']}",
        headers=owner,
        json={"ended_at": "2026-01-01T09:45:00+00:00", "duration_seconds": 2700},
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["duration_seconds"] == 2700
    assert stopped.json()["version"] == 2
    assert stopped.json()["started_at"] == entry["started_at"]


def test_a_patch_that_changes_nothing_keeps_the_version(client, owner):
    entry = create_entry(client, owner, notes="same").json()
    path = f"{TIME_ENTRIES}/{entry['id']}"
    unchanged = client.patch(path, headers=owner, json={"notes": "same"})
    assert unchanged.status_code == 200, unchanged.text
    assert unchanged.json()["version"] == 1
    changed = client.patch(path, headers=owner, json={"notes": "different"})
    assert changed.json()["version"] == 2


def test_a_stale_expected_version_is_refused(client, owner):
    entry = create_entry(client, owner).json()
    path = f"{TIME_ENTRIES}/{entry['id']}"
    client.patch(path, headers=owner, json={"notes": "first"})
    stale = client.patch(
        path, headers=owner, json={"notes": "second", "expected_version": 1}
    )
    assert stale.status_code == 409


def test_a_deleted_entry_is_gone(client, owner):
    entry = create_entry(client, owner).json()
    path = f"{TIME_ENTRIES}/{entry['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
    assert client.delete(path, headers=owner).status_code == 404
