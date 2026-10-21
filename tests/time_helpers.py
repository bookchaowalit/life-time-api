"""Shared helpers for the time-tracking domain tests."""

from typing import Any

TIME_ENTRIES = "/v1/time-entries"
TIME_LOGS = "/v1/time-logs"

START = "2026-01-01T09:00:00+00:00"
END = "2026-01-01T10:00:00+00:00"


def create_entry(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"task_id": 1, "started_at": START, **fields}
    return client.post(TIME_ENTRIES, headers=owner, json=body)


def create_log(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "log_date": "2026-01-01",
        "domain": "work",
        "activity": "coding",
        **fields,
    }
    return client.post(TIME_LOGS, headers=owner, json=body)
