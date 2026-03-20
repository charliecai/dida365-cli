# Dida CLI Command Reference

## Setup

| Command | Description |
|---|---|
| `dida setup [--json]` | Check environment: Python, uv, CLI version, auth status |

## Authentication

| Command | Description |
|---|---|
| `dida auth login` | Interactive OAuth login (opens browser) |
| `dida auth status [--json]` | Check authentication status |
| `dida auth logout` | Remove stored token |

## Task Management

### dida task create \<title\>

Create a new task.

| Option | Short | Description | Example |
|---|---|---|---|
| `--project` | `-P` | Project name or ID (fuzzy match) | `--project "work"` |
| `--content` | `-c` | Task notes/content | `--content "details"` |
| `--desc` | | Checklist description | |
| `--tags` | | Tags (comma-separated) | `--tags "work,urgent"` |
| `--all-day` | | All-day task | |
| `--start-date` | `-s` | Start date (today/tomorrow/YYYY-MM-DD/ISO) | `--start-date today` |
| `--due` | `-d` | Due date (today/tomorrow/YYYY-MM-DD/ISO) | `--due 2026-03-01` |
| `--timezone` | | Timezone (default: Asia/Shanghai) | |
| `--reminders` | | Reminders (comma-separated TRIGGER, e.g. TRIGGER:PT0S) | |
| `--repeat` | | Repeat rule (RRULE, e.g. RRULE:FREQ=DAILY;INTERVAL=1) | |
| `--priority` | `-p` | Priority: none/low/medium/high | `--priority high` |
| `--sort-order` | | Sort order value | |
| `--items` | | Subtasks JSON, e.g. `[{"title":"subtask1"}]` | |
| `--json` | | Output JSON format | |

### dida task get \<task_id\>

Show task details.

| Option | Description |
|---|---|
| `--project-id` | Project ID (skip auto-lookup) |
| `--json` | Output JSON format |

### dida task update \<task_id\>

Update an existing task. Supports all options from `task create` plus `--title`.

| Option | Short | Description |
|---|---|---|
| `--project-id` | | Project ID (skip auto-lookup) |
| `--title` | `-t` | New title |
| `--content` | `-c` | Task content |
| `--desc` | | Description |
| `--tags` | | Tags (comma-separated) |
| `--all-day` / `--no-all-day` | | All-day task toggle |
| `--start-date` | `-s` | Start date |
| `--due` | `-d` | Due date |
| `--timezone` | | Timezone |
| `--reminders` | | Reminders (comma-separated) |
| `--repeat` | | Repeat rule (RRULE) |
| `--priority` | `-p` | Priority: none/low/medium/high |
| `--sort-order` | | Sort order value |
| `--items` | | Subtasks (JSON) |
| `--json` | | Output JSON format |

### dida task complete \<task_id\>

Mark a task as complete.

| Option | Description |
|---|---|
| `--project-id` | Project ID (skip auto-lookup) |
| `--json` | Output JSON format |

### dida task delete \<task_id\>

Delete a task.

| Option | Short | Description |
|---|---|---|
| `--yes` | `-y` | Skip confirmation prompt |
| `--project-id` | | Project ID (skip auto-lookup) |
| `--json` | | Output JSON (skips confirmation) |

### dida task move \<task_id\>

Move a task to another project.

| Option | Short | Description |
|---|---|---|
| `--to` | `-T` | Destination project name or ID (required) |
| `--from` | `-F` | Source project name or ID |
| `--project-id` | | Source project ID (skip auto-lookup) |
| `--to-project-id` | | Destination project ID (skip fuzzy match) |
| `--json` | | Output JSON format |

### dida task filter

Filter and query tasks with advanced criteria.

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | Filter by project name or ID |
| `--start-date` | `-s` | Filter by start date |
| `--end-date` | `-e` | Filter by end date |
| `--priority` | `-p` | Filter by priority (comma-separated: none/low/medium/high) |
| `--tag` | | Filter by tags (comma-separated, AND logic) |
| `--status` | | Filter by status (comma-separated: normal/completed) |
| `--json` | | Output JSON format |

### dida task completed

List completed tasks within a time range.

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | Filter by project name or ID |
| `--start-date` | `-s` | Completed time range start |
| `--end-date` | `-e` | Completed time range end |
| `--json` | | Output JSON format |

## Project Management

### dida project list

List all projects.

| Option | Description |
|---|---|
| `--json` | Output JSON format |

### dida project get \<name-or-id\>

Show project details and tasks. Supports fuzzy name matching.

| Option | Description |
|---|---|
| `--json` | Output JSON format |

### dida project create \<name\>

Create a new project.

| Option | Description |
|---|---|
| `--color` | Color (e.g. #F18181) |
| `--view-mode` | View mode: list/kanban/timeline |
| `--kind` | Type: TASK/NOTE |
| `--sort-order` | Sort order value |
| `--json` | Output JSON format |

### dida project update \<project_id\>

Update a project.

| Option | Short | Description |
|---|---|---|
| `--name` | `-n` | New name |
| `--color` | | Color |
| `--view-mode` | | View mode: list/kanban/timeline |
| `--kind` | | Type: TASK/NOTE |
| `--sort-order` | | Sort order value |
| `--json` | | Output JSON format |

### dida project delete \<project_id\>

Delete a project.

| Option | Short | Description |
|---|---|---|
| `--yes` | `-y` | Skip confirmation |
| `--json` | | Output JSON format |

## JSON Output Format

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response

```json
{
  "error": "message",
  "code": "ERROR_CODE"
}
```

### Error Codes

| Code | Exit Code | Description |
|---|---|---|
| `AUTH_ERROR` | 2 | Not authenticated or token expired |
| `NOT_FOUND` | 1 | Task or project not found |
| `VALIDATION_ERROR` | 1 | Invalid input |
| `TIMEOUT` | 3 | Network timeout |
| `NETWORK_ERROR` | 3 | Network failure |
| `API_ERROR` | 1 | General API error |

## Priority Values

| CLI Value | API Value | Label |
|---|---|---|
| `none` | 0 | None |
| `low` | 1 | Low |
| `medium` / `mid` | 3 | Medium |
| `high` | 5 | High |

## Date Formats

Supported formats for `--due` and `--start-date`:
- `today` — end of today (23:59)
- `tomorrow` — end of tomorrow (23:59)
- `YYYY-MM-DD` — specific date at 23:59
- `YYYY-MM-DDTHH:MM` — specific date and time (ISO 8601)

Timezone: Asia/Shanghai (UTC+8) by default.
