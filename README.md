# Dida365 CLI & AI Agent Skill

CLI tool for managing Dida365 tasks via Open API v1, with an AI Agent skill (`/dida365`) for natural language task management.

## Architecture

```
┌──────────────────────────────┐
│  AI Agent Skill              │
│  /dida365 (SKILL.md)         │
│  Natural language → CLI      │
└──────────┬───────────────────┘
           │ calls
┌──────────▼───────────────────┐
│  dida CLI (typer)            │
│  dida task/project/auth      │
│  Human-readable + --json     │
└──────────┬───────────────────┘
           │ HTTP
┌──────────▼───────────────────┐
│  Dida365 Open API v1         │
│  api.dida365.com/open/v1     │
└──────────────────────────────┘
```

## Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager
- Dida365 developer account with OAuth app credentials
  - Register at [Dida365 Developer](https://developer.dida365.com/)
  - Create an app, set redirect URI to `http://localhost:18365/callback`
  - Note your Client ID and Client Secret

## Installation

### Method 1: Via AI Agent (Recommended)

If you're using an AI coding agent (Claude Code, Cursor, Windsurf, etc.):

1. Copy the `skill/dida365/` directory to your agent's skill directory (e.g., `~/.claude/skills/dida365/` for Claude Code)
2. Use the `/dida365` skill — the agent will automatically install the CLI and guide you through authentication

### Method 2: Manual Installation

```bash
git clone https://github.com/charliecai/dida365-cli.git && cd dida365-cli
./scripts/install.sh
```

This will:
1. Install the `dida` CLI via `uv pip install -e .`
2. Symlink the `/dida365` skill to `~/.claude/skills/dida365/`

### Verify Installation

```bash
dida setup
```

This checks Python version, uv availability, CLI installation, and authentication status.

## Authentication

```bash
dida auth login
```

Follow the prompts to enter your Client ID/Secret, then authorize in the browser. Token is stored at `~/.dida365/token.json` (permissions 0600).

```bash
dida auth status    # Check auth status
dida auth logout    # Remove stored token
```

## CLI Usage

### Tasks

```bash
# Create
dida task add "Buy milk" --priority high --due tomorrow --project "Shopping"

# List
dida task list                          # All tasks
dida task list --project "Work"         # By project

# Update
dida task update <task_id> --title "New title" --priority medium

# Complete
dida task done <task_id>

# Delete
dida task delete <task_id>              # With confirmation
dida task delete <task_id> --yes        # Skip confirmation

# Batch create (stdin JSON)
echo '[{"title":"Task 1"},{"title":"Task 2"}]' | dida task batch-add
```

### Projects

```bash
dida project list                       # List all projects
dida project show "Work"                # Show project with tasks (fuzzy match)
```

### JSON Output

All list/action commands support `--json` for structured output:

```bash
dida task list --json
# {"success": true, "data": [...]}

dida task add "Test" --json
# {"success": true, "data": {"id": "...", "title": "Test", ...}}
```

## AI Agent Skill

After installation, use `/dida365` in your AI agent:

```
/dida365 show my work tasks
/dida365 add "Submit report" due tomorrow, high priority
/dida365 mark the report task as done
/dida365 what projects do I have
```

The agent will translate your natural language to `dida` CLI commands and present the results.

**Supported agents:** Any AI coding agent that can execute shell commands (Claude Code, Cursor, Windsurf, etc.)

## Development

```bash
uv sync --dev                    # Install dev dependencies
uv run ruff check src/ tests/    # Lint
uv run ruff format src/ tests/   # Format
uv run pytest tests/ -v          # Run tests
```

## Known Limitations

1. **API Rate Limit** — Dida365 Open API limits to 100 requests/minute. Operations like `task done` and `task delete` need to search all projects to find a task's project ID, which can hit this limit if you have many projects.

2. **No Inbox API** — The Open API has no direct "inbox" endpoint. `dida task list` (without `--project`) fetches tasks from all projects, which is slow with many projects.

3. **API Beta Status** — The Dida365 Open API is still in Beta. Endpoints may change without notice.

4. **No Tag Support** — The Open API does not expose tag/label management.

5. **No Habit Tracking** — The Open API does not support habit/punch-in features.

6. **Token Refresh** — If the refresh token expires, you'll need to re-run `dida auth login`.

## FAQ

**Q: How do I get Client ID and Client Secret?**
A: Register at [Dida365 Developer](https://developer.dida365.com/), create an app, and set the redirect URI to `http://localhost:18365/callback`.

**Q: `dida auth login` opens the browser but nothing happens?**
A: Make sure port 18365 is not in use. The CLI starts a local HTTP server on that port to receive the OAuth callback.

**Q: Commands are slow or hit rate limits?**
A: If you have many projects, operations that search for a task (done, delete, update) need to iterate through all projects. Consider using `--project` flag to narrow the search scope in future versions.

**Q: Can I use this with TickTick (international version)?**
A: Currently configured for Dida365 (`api.dida365.com`). To use with TickTick international, you would need to change the API base URL to `api.ticktick.com` and OAuth URLs to `ticktick.com`.
