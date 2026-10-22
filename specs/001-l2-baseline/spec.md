# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/life-time-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, the only tests were the generic contract suite, and the API stored a time entry that ended before it started.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An entry cannot end before it started

- **Given** an owner with write permission
- **When** they create a time entry with `started_at` 2026-01-01T10:00 and `ended_at` 2026-01-01T09:00
- **Then** the API answers 422 `invalid_value` naming both fields; the same moment for both is accepted
- **Test:** `tests/test_time_entry_validation.py::test_an_entry_cannot_end_before_it_started` · level: integration (API + throwaway PostgreSQL)

### AC-02 — Moving the end before the start is refused on update

- **Given** an entry from 09:00 to 10:00
- **When** a patch sets `ended_at` to 08:00
- **Then** the API answers 422 and the stored `ended_at` and version are unchanged; a patch that touches neither time still succeeds
- **Test:** `tests/test_time_entry_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-03 — Moving the start after the end is refused on update

- **Given** an entry from 09:00 to 10:00
- **When** a patch sets `started_at` to 11:00
- **Then** the API answers 422 and the stored `started_at` is unchanged
- **Test:** `tests/test_time_entry_validation.py::test_moving_the_start_after_the_end_is_refused_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-04 — A new entry is a manual, running entry

- **Given** a create request with only `task_id` and `started_at`
- **When** the entry is created
- **Then** `source` is manual, `ended_at` and `duration_seconds` are empty and `version` is 1
- **Test:** `tests/test_time_entry_defaults.py::test_new_entry_defaults_to_a_manual_running_entry` · level: integration (API + throwaway PostgreSQL)

### AC-05 — A task can have many entries; imports keep the old id once

- **Given** a task with an entry, and an entry imported with `legacy_id` 4321
- **When** a second entry is added for the task and the same `legacy_id` is imported again
- **Then** the second entry is created; the import keeps id 4321 and the repeat is refused with 409
- **Test:** `tests/test_time_entry_defaults.py::test_an_import_keeps_the_old_id_and_refuses_a_second_import` · level: integration (API + throwaway PostgreSQL)

### AC-06 — Entries list and group by task only

- **Given** entries for several tasks
- **When** the owner lists by `task_id`, asks for running entries, and asks for stats by `task_id` or by `source`
- **Then** only that task's entries are listed, `null=ended_at` returns running ones, stats count per task, and grouping by `source` is refused with 422
- **Test:** `tests/test_time_entry_queries.py` · level: integration (API + throwaway PostgreSQL)

### AC-07 — A log needs a date, a domain and an activity

- **Given** a create request for a time log
- **When** a required text is missing or empty, or `minutes` is not a whole number
- **Then** the API answers 422; a valid log defaults `minutes` to 0
- **Test:** `tests/test_time_log_validation.py::test_required_text_cannot_be_empty` · level: integration (API + throwaway PostgreSQL)

### AC-08 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `POST /v1/time-entries`, `PATCH /v1/time-entries/{id}` | changed | `ended_at` before `started_at` -> `422 {"error": "invalid_value", "fields": ["ended_at", "started_at"]}` |
| `cell.yaml` | changed | new resource key `ranges: [[started_at, ended_at]]` on time-entry |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "56"` (measured 58.25% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_time_entry_validation.py::test_an_entry_cannot_end_before_it_started` | b97f1fc · `.venv/bin/pytest -q tests/test_time_entry_validation.py::test_an_entry_cannot_end_before_it_started` · `assert 201 == 422` | CI run of the pushed tip | none |
| AC-02 | `tests/test_time_entry_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` | b97f1fc · `.venv/bin/pytest -q tests/test_time_entry_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · `assert 200 == 422` | CI run of the pushed tip | none |
| AC-03 | `tests/test_time_entry_validation.py::test_moving_the_start_after_the_end_is_refused_on_update` | b97f1fc · `.venv/bin/pytest -q tests/test_time_entry_validation.py::test_moving_the_start_after_the_end_is_refused_on_update` · `assert 200 == 422` | CI run of the pushed tip | none |
| AC-04 | `tests/test_time_entry_defaults.py::test_new_entry_defaults_to_a_manual_running_entry` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_time_entry_defaults.py::test_an_import_keeps_the_old_id_and_refuses_a_second_import` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_time_entry_queries.py` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_time_log_validation.py::test_required_text_cannot_be_empty` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_contract.py::test_numbers_fit_their_columns` | ef75d70 · `.venv/bin/pytest -q -k numbers_fit` · `psycopg.errors.NumericValueOutOfRange: integer out of range` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
