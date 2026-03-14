# Dida365 CLI & AI Agent Skill

通过 AI Agent 自然语言管理滴答清单 (Dida365) 任务，底层基于 Dida365 Open API v1。

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

## Quick Start

### Step 1: Install Skill

将 `skill/dida365/` 目录安装到你的 AI Agent 的 skills 目录：

**Claude Code:**
```bash
git clone https://github.com/charliecai/dida365-cli.git ~/.local/share/dida365-cli
ln -s ~/.local/share/dida365-cli/skill/dida365 ~/.claude/skills/dida365
```

**Other agents (Cursor, Windsurf, etc.):**
将 `skill/dida365/SKILL.md` 复制到对应 agent 的 skill/prompt 目录。

### Step 2: Use the Skill

安装 Skill 后，直接在 AI Agent 中使用 `/dida365`：

```
/dida365 show my tasks
```

首次使用时，Agent 会自动检测并完成以下步骤：
1. 安装 `dida` CLI（如果尚未安装）
2. 检查认证状态，引导你完成 Dida365 OAuth 认证

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager
- Dida365 developer account — 前往 [developer.dida365.com](https://developer.dida365.com/) 注册应用，设置回调地址为 `http://localhost:18365/callback`

## Manual Setup (without AI Agent)

如果不通过 AI Agent，也可以手动安装：

```bash
git clone https://github.com/charliecai/dida365-cli.git && cd dida365-cli
./scripts/install.sh
dida setup    # 检查环境并引导认证
```

## Authentication

```bash
dida auth login     # OAuth 认证（交互式）
dida auth status    # 查看认证状态
dida auth logout    # 登出
```

Token 存储在 `~/.dida365/token.json`（权限 0600）。

## CLI Usage

### Tasks

```bash
dida task add "Buy milk" --priority high --due tomorrow --project "Shopping"
dida task list                          # All tasks
dida task list --project "Work"         # By project
dida task update <task_id> --title "New title" --priority medium
dida task done <task_id>
dida task delete <task_id>              # With confirmation
dida task delete <task_id> --yes        # Skip confirmation
echo '[{"title":"Task 1"},{"title":"Task 2"}]' | dida task batch-add
```

### Projects

```bash
dida project list                       # List all projects
dida project show "Work"                # Show project with tasks
```

### JSON Output

All commands support `--json` for structured output:

```bash
dida task list --json
# {"success": true, "data": [...]}
```

## AI Agent Skill

安装 Skill 后，支持自然语言操作：

```
/dida365 show my work tasks
/dida365 add "Submit report" due tomorrow, high priority
/dida365 mark the report task as done
/dida365 what projects do I have
```

**Supported agents:** Claude Code, Cursor, Windsurf, 以及任何能执行 shell 命令的 AI Agent。

## Development

```bash
uv sync --dev                    # Install dev dependencies
uv run ruff check src/ tests/    # Lint
uv run ruff format src/ tests/   # Format
uv run pytest tests/ -v          # Run tests
```

## Known Limitations

1. **API Rate Limit** — 100 requests/minute。使用 `--project-id` 可减少 API 调用。
2. **No Inbox API** — 无直接收件箱接口，`dida task list` 需遍历所有项目。
3. **API Beta Status** — Dida365 Open API 仍为 Beta。
4. **No Tag Support** — API 不支持标签管理。
5. **No Habit Tracking** — API 不支持打卡/习惯功能。

## FAQ

**Q: 如何获取 Client ID 和 Client Secret?**
A: 前往 [developer.dida365.com](https://developer.dida365.com/) 注册应用，设置回调地址为 `http://localhost:18365/callback`。

**Q: `dida auth login` 打开浏览器后没有反应?**
A: 确保端口 18365 未被占用。

**Q: 可以用于 TickTick 国际版吗?**
A: 当前配置为 Dida365 (`api.dida365.com`)。使用国际版需修改 API 地址为 `api.ticktick.com`。
