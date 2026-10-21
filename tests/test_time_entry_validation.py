"""What a time entry refuses: missing fields, bad types, unknown fields and backwards ranges."""

from time_helpers import END, START, TIME_ENTRIES, create_entry


def test_task_id_is_required(client, owner):
    response = client.post(TIME_ENTRIES, headers=owner, json={"started_at": START})
    assert response.status_code == 422


def test_started_at_is_required(client, owner):
    response = client.post(TIME_ENTRIES, headers=owner, json={"task_id": 1})
    assert response.status_code == 422


def test_started_at_must_be_a_timestamp(client, owner):
    assert create_entry(client, owner, started_at="yesterday").status_code == 422


def test_ended_at_must_be_a_timestamp(client, owner):
    assert create_entry(client, owner, ended_at="later").status_code == 422


def test_task_id_must_be_a_whole_number(client, owner):
    assert create_entry(client, owner, task_id="soon").status_code == 422


def test_duration_must_be_a_whole_number_of_seconds(client, owner):
    assert create_entry(client, owner, duration_seconds="an hour").status_code == 422
    assert create_entry(client, owner, duration_seconds=3600).status_code == 201


def test_an_unknown_field_is_refused(client, owner):
    assert create_entry(client, owner, colour="red").status_code == 422


def test_an_entry_cannot_end_before_it_started(client, owner):
    backwards = create_entry(client, owner, started_at=END, ended_at=START)
    assert backwards.status_code == 422, backwards.text
    assert backwards.json()["detail"] == {
        "error": "invalid_value",
        "fields": ["ended_at", "started_at"],
    }


def test_an_entry_may_start_and_end_at_the_same_moment(client, owner):
    instant = create_entry(client, owner, started_at=START, ended_at=START)
    assert instant.status_code == 201, instant.text


def test_a_running_entry_has_no_end_yet(client, owner):
    running = create_entry(client, owner)
    assert running.status_code == 201, running.text
    assert running.json()["ended_at"] is None


def test_moving_the_end_before_the_start_is_refused_on_update(client, owner):
    entry = create_entry(client, owner, started_at=START, ended_at=END).json()
    path = f"{TIME_ENTRIES}/{entry['id']}"
    refused = client.patch(
        path, headers=owner, json={"ended_at": "2026-01-01T08:00:00+00:00"}
    )
    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"]["fields"] == ["ended_at", "started_at"]
    stored = client.get(path, headers=owner).json()
    assert stored["ended_at"] == entry["ended_at"]
    assert stored["version"] == 1


def test_moving_the_start_after_the_end_is_refused_on_update(client, owner):
    entry = create_entry(client, owner, started_at=START, ended_at=END).json()
    path = f"{TIME_ENTRIES}/{entry['id']}"
    refused = client.patch(
        path, headers=owner, json={"started_at": "2026-01-01T11:00:00+00:00"}
    )
    assert refused.status_code == 422, refused.text
    assert client.get(path, headers=owner).json()["started_at"] == entry["started_at"]


def test_a_patch_that_touches_neither_time_still_works(client, owner):
    entry = create_entry(client, owner, started_at=START, ended_at=END).json()
    renamed = client.patch(
        f"{TIME_ENTRIES}/{entry['id']}", headers=owner, json={"notes": "standup"}
    )
    assert renamed.status_code == 200, renamed.text


def test_task_id_cannot_be_cleared(client, owner):
    entry = create_entry(client, owner).json()
    cleared = client.patch(
        f"{TIME_ENTRIES}/{entry['id']}", headers=owner, json={"task_id": None}
    )
    assert cleared.status_code == 422
