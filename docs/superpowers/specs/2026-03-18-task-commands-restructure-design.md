# Task Commands Restructure: Remove list, Add move/filter/completed

**Date:** 2026-03-18
**Status:** Approved

## Summary

Remove `dida task list` command. Add three new commands mapping to Dida365 Open API endpoints:
- `dida task move` → `POST /open/v1/task/move`
- `dida task filter` → `POST /open/v1/task/filter`
- `dida task completed` → `POST /open/v1/task/completed`

Audit existing commands for parameter completeness. Update docs and bump versions.

## Changes

### 1. Remove `dida task list`

Delete `task_list()` function from `src/dida/cli.py`. This command was implemented via client-side iteration over all projects (no dedicated API endpoint). `dida task filter` replaces it with server-side filtering.

### 2. New Command: `dida task move`

**API:** `POST /open/v1/task/move`
**Description:** Move a task between projects.

```
dida task move <task_id> --to <project_name_or_id> [options] [--json]
```

| Option | Short | Description | Required |
|---|---|---|---|
| `task_id` | | Task ID (positional argument) | Yes |
| `--to` | `-T` | Destination project name or ID (fuzzy match) | Yes |
| `--from` | `-F` | Source project name or ID (optional, auto-detected) | No |
| `--project-id` | | Source project ID (skip auto-lookup) | No |
| `--to-project-id` | | Destination project ID (skip fuzzy match) | No |

**API request body:** JSON array `[{taskId, fromProjectId, toProjectId}]`
**API response:** Array of `{taskId, etag}` results.

**Client method:** `move_task(task_id: str, from_project_id: str, to_project_id: str) -> dict`

**Resolution logic:**
1. If `--project-id` provided, use as `fromProjectId`; else if `--from` provided, resolve via fuzzy match; else auto-detect via `find_task_project_id()`
2. If `--to-project-id` provided, use as `toProjectId`; else resolve `--to` via fuzzy match
3. Error if neither `--to` nor `--to-project-id` is provided
4. `--project-id` exists for consistency with other commands (task update/delete/complete) — allows agents to skip auto-lookup when project ID is already known

### 3. New Command: `dida task filter`

**API:** `POST /open/v1/task/filter`
**Description:** Filter tasks with advanced criteria. Replaces `task list`.

```
dida task filter [options] [--json]
```

| Option | Short | Description | Schema |
|---|---|---|---|
| `--project` | `-P` | Project name or ID (fuzzy match → projectIds) | list |
| `--start-date` | `-s` | Filter tasks where startDate ≥ value | date |
| `--end-date` | `-e` | Filter tasks where startDate ≤ value | date |
| `--priority` | `-p` | Priority levels, comma-separated (none/low/medium/high) | list |
| `--tag` | | Tags, comma-separated (AND logic per API: "contain all of the specified tags") | list |
| `--status` | | Status codes, comma-separated (normal/completed) | list |

**API request body:** `{projectIds?, startDate?, endDate?, proiority?, tag?, status?}`
Note: API field is misspelled as `proiority` — we must send it as-is.

**Priority value mapping (CLI → API):** none=0, low=1, medium=3, high=5 (same as existing commands).
**Status value mapping (CLI → API):** normal=[0], completed=[2].

**Note:** `task filter --status completed` overlaps with `task completed` — this is intentional. `task completed` filters by `completedTime` range while `task filter` filters by task `startDate` range.

**Client method:** `filter_tasks(project_ids=None, start_date=None, end_date=None, priority=None, tags=None, status=None) -> list[Task]`

### 4. New Command: `dida task completed`

**API:** `POST /open/v1/task/completed`
**Description:** List completed tasks within a time range.

```
dida task completed [options] [--json]
```

| Option | Short | Description | Schema |
|---|---|---|---|
| `--project` | `-P` | Project name or ID (fuzzy match → projectIds) | list |
| `--start-date` | `-s` | completedTime ≥ value | date |
| `--end-date` | `-e` | completedTime ≤ value | date |

**API request body:** `{projectIds?, startDate?, endDate?}`

**Client method:** `list_completed_tasks(project_ids=None, start_date=None, end_date=None) -> list[Task]`

### 5. Parameter Audit

Existing commands vs API parameters:

| Command | API Params | CLI Params | Gap |
|---|---|---|---|
| task create | title, content, desc, tags, isAllDay, startDate, dueDate, timeZone, reminders, repeatFlag, priority, sortOrder, items | All covered | None |
| task update | id, projectId, title, content, desc, isAllDay, startDate, dueDate, timeZone, reminders, repeatFlag, priority, sortOrder, items | All covered | None |
| task get | projectId, taskId | Both covered | None |
| task complete | projectId, taskId | Both covered | None |
| task delete | projectId, taskId | Both covered | None |
| task batch-create | Array of task objects | Stdin JSON | None |
| project create | name, color, sortOrder, viewMode, kind | All covered | None |
| project update | name, color, sortOrder, viewMode, kind | All covered | None |
| project get | projectId | Covered (with fuzzy match) | None |
| project list | (none) | N/A | None |
| project delete | projectId | Covered | None |

**Conclusion:** No parameter gaps in existing commands.

### 6. Documentation & Version Updates

After all code changes:

1. **README.md** — Remove `task list` examples, add `task move`/`task filter`/`task completed` sections with examples and parameter tables. Update Known Limitations (remove "No Inbox API" note since filter replaces list). Update Deprecated Commands table.
2. **skill/dida365/SKILL.md** — Update command reference: remove `task list`, add three new commands with full option tables. Bump version to `0.3.0`.
3. **skill/dida365/references/api-ref.md** — Remove `task list`, add three new command references.
4. **pyproject.toml** — Bump version from `0.2.0` to `0.3.0`.
5. **src/dida/cli.py** — Update `__version__` if defined inline.

## Files to Modify

| File | Action |
|---|---|
| `src/dida/client.py` | Add `move_task()`, `filter_tasks()`, `list_completed_tasks()` |
| `src/dida/cli.py` | Remove `task_list()`, add `task_move()`, `task_filter()`, `task_completed()` |
| `tests/test_cli_commands.py` | Remove list tests, add move/filter/completed tests |
| `tests/test_client.py` | Add client method tests |
| `README.md` | Update task section, examples, limitations |
| `skill/dida365/SKILL.md` | Update command reference, bump version |
| `skill/dida365/references/api-ref.md` | Remove `task list` section, add `task move`/`task filter`/`task completed` with full option tables matching the format of existing commands |
| `pyproject.toml` | Bump version to 0.3.0 |
