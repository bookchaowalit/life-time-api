"""Defaults, imports and repeated writes of a time entry."""

from time_helpers import START, TIME_ENTRIES, create_entry


def test_new_entry_defaults_to_a_manual_running_entry(client, owner):
    response = create_entry(client, owner, task_id=42)
    assert response.status_code == 201, response.text
    entry = response.json()
    assert entry["source"] == "manual"
    assert entry["ended_at"] is None
    assert entry["duration_seconds"] is None
    assert entry["notes"] is None
    assert entry["task_id"] == 42
    assert entry["version"] == 1


def test_the_source_can_be_set_on_create(client, owner):
    entry = create_entry(client, owner, source="timer").json()
    assert entry["source"] == "timer"


def test_the_same_task_can_have_many_entries(client, owner):
    first = create_entry(client, owner, task_id=7)
    second = create_entry(client, owner, task_id=7)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]


def test_an_import_keeps_the_old_id_and_refuses_a_second_import(client, owner):
    imported = create_entry(client, owner, legacy_id=4321)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 4321
    assert imported.json()["legacy_id"] == 4321
    found = client.get(f"{TIME_ENTRIES}/legacy/4321", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 4321
    assert create_entry(client, owner, legacy_id=4321).status_code == 409


def test_an_unknown_old_id_is_not_found(client, owner):
    assert client.get(f"{TIME_ENTRIES}/legacy/987654", headers=owner).status_code == 404


def test_an_import_may_carry_the_old_timestamps(client, owner):
    imported = create_entry(
        client,
        owner,
        legacy_id=4322,
        created_at="2025-06-01T00:00:00+00:00",
        updated_at="2025-06-02T00:00:00+00:00",
    )
    assert imported.status_code == 201, imported.text
    assert imported.json()["created_at"].startswith("2025-06-01")


def test_a_retried_create_with_the_same_key_makes_one_entry(client, owner):
    headers = {**owner, "Idempotency-Key": "time-entry-key-0001"}
    body = {"task_id": 5, "started_at": START}
    first = client.post(TIME_ENTRIES, headers=headers, json=body)
    again = client.post(TIME_ENTRIES, headers=headers, json=body)
    assert first.status_code == 201, first.text
    assert again.status_code == 201, again.text
    assert again.json()["id"] == first.json()["id"]
