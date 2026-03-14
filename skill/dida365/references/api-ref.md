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

### dida task add \<title\>

Create a new task.

| Option | Short | Description | Example |
|---|---|---|---|
| `--priority` | `-p` | Priority: none/low/medium/high | `--priority high` |
| `--due` | `-d` | Due date: today/tomorrow/YYYY-MM-DD/ISO 8601 | `--due 2026-03-01` |
| `--project` | `-P` | Project name or ID (fuzzy match) | `--project "work"` |
| `--content` | `-c` | Task notes/content | `--content "details"` |
| `--json` | | Output JSON format | |

### dida task list

List tasks.

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | Filter by project name or ID |
| `--all` | | Include tasks from closed projects |
| `--json` | | Output JSON format |

### dida task update \<task_id\>

Update an existing task.

| Option | Short | Description |
|---|---|---|
| `--title` | `-t` | New title |
| `--priority` | `-p` | New priority |
| `--due` | `-d` | New due date |
| `--content` | `-c` | New content |
| `--project-id` | | Project ID (skip auto-lookup) |
| `--json` | | Output JSON format |

### dida task done \<task_id\>

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

### dida task batch-add

Batch create tasks from stdin JSON.

Input format: `[{"title": "Task 1", "priority": 5}, {"title": "Task 2"}]`

| Option | Description |
|---|---|
| `--json` | Output JSON format |

## Project Management

### dida project list

List all projects.

| Option | Description |
|---|---|
| `--json` | Output JSON format |

### dida project show \<name-or-id\>

Show project details and tasks. Supports fuzzy name matching.

| Option | Description |
|---|---|
| `--json` | Output JSON format |

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

Supported formats for `--due`:
- `today` — end of today (23:59)
- `tomorrow` — end of tomorrow (23:59)
- `YYYY-MM-DD` — specific date at 23:59
- `YYYY-MM-DDTHH:MM` — specific date and time (ISO 8601)

Timezone: Asia/Shanghai (UTC+8) by default.
