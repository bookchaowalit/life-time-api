# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through the cell's own MCP server (`time-mcp`, tools
  `time.<resource>.list|get|create|update|delete`) and the hosted tool hub
  (`platform-mcp-remote-worker`, which lists this service's host in its allow-list).
- Local tooling that reads the cell through `EMPIRE_TIME_API`: `ops-toolkit` (`cell_store.py`) and
  `mcp-aggregator` (`cell-store.ts`), as recorded in the online-systems registry.
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `time.time-entry:read|write|delete` and `time.time-log:read|write|delete`.
- A web page in `life-dashboard-web` that shows time: [ต้องยืนยัน].

## Product Purpose

Record how long the owner spent, in two forms: a time entry (a start, an optional end and a
duration against one task) and a time log (a day, a domain, an activity and minutes). The domain
had no rows when it left the control plane (2026-10-11), so the cell starts empty and new
features are built here.

Success: each stretch of work is recorded once against its task, and a stopped entry never ends
before it started.

## Positioning

One capability, one service: its own API (Railway, serverless), its own database (Neon) with
row-level security per workspace, and authorization, executions and audit through
`empire-platform`. It is workspace-scoped, so the same service can serve other tenants without
code changes.

## Operating Context

- Production: `https://time-api-production-2050.up.railway.app` (`/health`), deployed by merging
  to `main` after CI.
- Data starts empty (the retired SQLite tables had no rows); imports keep old ids in `legacy_id`.
- Monitored by `platform-uptime-worker` (target `time-api`); errors go to Sentry without personal
  data.

## Capabilities and Constraints

- `/v1/time-entries`: list (filter `task_id`; also `id`, `legacy_id`, `updated_since`, `null`,
  `order`, `limit`, `offset`), stats (grouped by `task_id` only), get, get-by-legacy-id, create
  (with `Idempotency-Key`), patch (with `expected_version`), delete.
- `/v1/time-logs`: the same routes, with no filter, so stats are always refused.
- Time entry rules: `task_id` (a plain number, not a foreign key to a task service) and
  `started_at` are required; `ended_at` is empty while the timer runs; `source` defaults to
  `manual`; `ended_at` cannot be before `started_at` (422 `invalid_value` naming both fields, on
  create and on patch; the same moment is allowed); `duration_seconds` is stored as given, not
  computed from the two times.
- Time log rules: `log_date`, `domain` and `activity` are required text that cannot be empty
  (`log_date` is text, not a date); `minutes` is a whole number defaulting to 0.
- No uniqueness rules: the same task can have many entries and the same activity can be logged
  twice on one day. An import with a `legacy_id` already used is refused with 409.
- Unknown fields are refused (422); an unchanged patch keeps the version.
- Out of scope: totals and reports over time, timers that stop themselves, and checking that
  `task_id` exists.

## Measures

Proposed, nothing collects them yet:

- Time entries created per week, and the share that carry an `ended_at`.
- Entries still running (no `ended_at`) older than 24 hours.
- 5xx rate and p95 latency on `/v1/time-entries` (Sentry and uptime worker).
