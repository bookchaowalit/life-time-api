# time-tracking

The Time tracking cell: its own API (Railway, serverless) and its own Neon
database, described by `cell.yaml` and served by the code in `src/cellkit/`, which
this repository owns. It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `time-tracking`, service `time-api` (Serverless) |
| Data | Neon project `time-tracking`, database `time` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`time`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `time.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/time-entries` | time-entry | `task_id` |
| `/v1/time-logs` | time-log | — |

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/time-db provision
npm install && railway config apply && railway up --ci --service time-api
railway scale --service time-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `TIME_DB_MODE=hosted`, `TIME_DB_URL_API`,
`TIME_JWT_PUBLIC_KEY_PEM`, `TIME_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
