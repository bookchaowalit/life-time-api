"""What a time log refuses: empty required text, bad numbers and unknown fields."""

from time_helpers import TIME_LOGS, create_log


def test_log_date_is_required(client, owner):
    body = {"domain": "work", "activity": "coding"}
    assert client.post(TIME_LOGS, headers=owner, json=body).status_code == 422


def test_domain_is_required(client, owner):
    body = {"log_date": "2026-01-01", "activity": "coding"}
    assert client.post(TIME_LOGS, headers=owner, json=body).status_code == 422


def test_activity_is_required(client, owner):
    body = {"log_date": "2026-01-01", "domain": "work"}
    assert client.post(TIME_LOGS, headers=owner, json=body).status_code == 422


def test_required_text_cannot_be_empty(client, owner):
    assert create_log(client, owner, log_date="").status_code == 422
    assert create_log(client, owner, domain="").status_code == 422
    assert create_log(client, owner, activity="").status_code == 422


def test_required_text_cannot_be_emptied_on_update(client, owner):
    log = create_log(client, owner).json()
    path = f"{TIME_LOGS}/{log['id']}"
    assert client.patch(path, headers=owner, json={"activity": ""}).status_code == 422
    assert client.patch(path, headers=owner, json={"domain": None}).status_code == 422
    assert client.get(path, headers=owner).json()["activity"] == "coding"


def test_minutes_must_be_a_whole_number(client, owner):
    assert create_log(client, owner, minutes="a while").status_code == 422
    assert create_log(client, owner, minutes=1.5).status_code == 422
    assert create_log(client, owner, minutes=90).status_code == 201


def test_an_unknown_field_is_refused(client, owner):
    assert create_log(client, owner, mood="good").status_code == 422
