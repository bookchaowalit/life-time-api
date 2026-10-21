"""Listing, grouping and the lifecycle of a time log."""

from time_helpers import TIME_LOGS, create_log


def test_list_returns_logs_in_creation_order(client, owner):
    ids = [
        create_log(client, owner, activity=f"step {n}").json()["id"] for n in range(3)
    ]
    listed = client.get(TIME_LOGS, headers=owner, params={"id": ids})
    assert [item["id"] for item in listed.json()["items"]] == ids


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(TIME_LOGS, headers=owner, params={"domain": "work"})
    assert listed.status_code == 422


def test_stats_have_no_grouping_because_logs_declare_no_filters(client, owner):
    create_log(client, owner)
    for field in ("domain", "log_date", "activity"):
        stats = client.get(
            f"{TIME_LOGS}/stats", headers=owner, params={"group_by": field}
        )
        assert stats.status_code == 422, field


def test_correcting_the_minutes_bumps_the_version(client, owner):
    log = create_log(client, owner, minutes=10).json()
    path = f"{TIME_LOGS}/{log['id']}"
    fixed = client.patch(path, headers=owner, json={"minutes": 25})
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["minutes"] == 25
    assert fixed.json()["version"] == 2
    unchanged = client.patch(path, headers=owner, json={"minutes": 25})
    assert unchanged.json()["version"] == 2


def test_a_deleted_log_is_gone(client, owner):
    log = create_log(client, owner).json()
    path = f"{TIME_LOGS}/{log['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
