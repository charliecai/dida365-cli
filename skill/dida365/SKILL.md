---
name: dida365
description: >
  Manage Dida365 (滴答清单) tasks and projects via natural language.
  Use when user wants to create, view, update, complete, delete, or move tasks/projects in Dida365.
  Also triggers for: batch creating tasks, filtering tasks by priority/date/tag/status,
  checking completed tasks, listing projects, or any todo/task management request
  mentioning Dida365 or 滴答清单.
---

# Dida365 Task Manager

Translate natural language requests into `dida` CLI commands.
For full command options and parameters, see [references/api-ref.md](references/api-ref.md).

## Environment Bootstrap (run before any command)

1. Check if `dida` CLI is installed:
```bash
which dida
```

If NOT found, install automatically:
```bash
# Requires uv — https://docs.astral.sh/uv/
if [ -d "$HOME/.local/share/dida365-cli" ]; then
  git -C "$HOME/.local/share/dida365-cli" pull
else
  git clone https://github.com/charliecai/dida365-cli.git "$HOME/.local/share/dida365-cli"
fi
uv pip install -e "$HOME/.local/share/dida365-cli"
dida --version
```

2. Check authentication:
```bash
dida auth status --json
```

If `{"authenticated": false}`, tell the user to:
1. Register a developer app at https://developer.dida365.com/
2. Set redirect URI to `http://localhost:18365/callback`
3. Run `dida auth login` in their terminal (requires interactive browser — do NOT run it yourself)

Shortcut: `dida setup --json` checks everything at once. If `"ok": true`, proceed.

## Core Principles

1. **Always use `--json` flag** for reliable output parsing.
2. **Present results in human-friendly format** after parsing JSON.
3. **Resolve project names** via `--project <name>` (CLI handles fuzzy matching).
4. **Confirm destructive actions** with the user BEFORE running delete commands.
5. **Always pass `--project-id`** when completing, updating, or deleting tasks — first capture `projectId` from a filter/get, then pass it to avoid slow full-project scans.

## Priority Inference

| User language | Priority |
|---|---|
| "urgent", "ASAP", "critical" | high |
| "important", "should" | medium |
| "when you can", "low priority", "eventually" | low |
| (no urgency mentioned) | none |

## Workflow Patterns

### Two-step flow (complete/update/delete)

Always filter first to get `id` and `projectId`, then operate:

```bash
# 1. Find the task
dida task filter --json

# 2. Operate with --project-id
dida task complete <task_id> --project-id <project_id> --json
```

### Examples

**Create a task:**
User: "remind me to buy milk tomorrow, high priority"
```bash
dida task create "buy milk" --priority high --due tomorrow --json
```

**Complete a task by description:**
User: "I finished the report"
1. `dida task filter --json` → find matching task
2. `dida task complete <id> --project-id <pid> --json`

**Batch create with project:**
User: "add eggs, bread, cheese to my shopping list"
1. `dida project list --json` → resolve project ID
2. `echo '[{"title":"eggs","projectId":"<id>"},...]' | dida task batch-create --json`

**Move a task:**
User: "move that task to my work project"
```bash
dida task move <task_id> --to "work" --project-id <source_pid> --json
```

## Response Format

- For task lists: summarize by priority/due date, highlight overdue items
- For create/update/complete: confirm what was done with key details
- For errors: explain in plain language and suggest fixes
