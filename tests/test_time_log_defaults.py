"""Defaults, imports and repeated writes of a time log."""

from time_helpers import TIME_LOGS, create_log


def test_new_log_defaults_to_zero_minutes(client, owner):
    response = create_log(client, owner)
    assert response.status_code == 201, response.text
    log = response.json()
    assert log["minutes"] == 0
    assert log["notes"] is None
    assert log["version"] == 1


def test_a_log_keeps_the_text_it_was_given(client, owner):
    log = create_log(
        client, owner, log_date="2026-02-03", domain="study", activity="reading"
    ).json()
    assert (log["log_date"], log["domain"], log["activity"]) == (
        "2026-02-03",
        "study",
        "reading",
    )


def test_the_same_activity_can_be_logged_twice_on_one_day(client, owner):
    assert create_log(client, owner, activity="walk").status_code == 201
    assert create_log(client, owner, activity="walk").status_code == 201


def test_an_import_keeps_the_old_id_and_refuses_a_second_import(client, owner):
    imported = create_log(client, owner, legacy_id=8765, minutes=30)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 8765
    found = client.get(f"{TIME_LOGS}/legacy/8765", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["minutes"] == 30
    assert create_log(client, owner, legacy_id=8765).status_code == 409
