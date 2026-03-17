# Dida365 CLI & AI Agent Skill

通过 AI Agent 自然语言管理滴答清单 (Dida365) 任务和项目，底层基于 Dida365 Open API v1。

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
# 创建任务 (支持所有 API 参数)
dida task create "Buy milk" --priority high --due tomorrow --project "Shopping"
dida task create "Weekly meeting" --repeat "RRULE:FREQ=WEEKLY;INTERVAL=1" --all-day
dida task create "Big task" --items '[{"title":"Step 1"},{"title":"Step 2"}]'
dida task create "Tagged" --tags "work,urgent" --start-date 2026-03-20

# 查看任务
dida task list                                    # 所有活跃任务
dida task list --project "Work"                   # 按项目
dida task list --priority high                    # 按优先级
dida task list --status completed                 # 已完成任务
dida task list --tag "urgent" --limit 10          # 按标签，限制数量

# 查看单个任务
dida task get <task_id> --project-id <project_id>

# 更新任务 (支持所有 API 参数)
dida task update <task_id> --title "New title" --priority medium
dida task update <task_id> --due 2026-04-01 --tags "updated"

# 完成/删除
dida task complete <task_id>
dida task delete <task_id>                        # 带确认
dida task delete <task_id> --yes                  # 跳过确认

# 批量创建
echo '[{"title":"Task 1"},{"title":"Task 2"}]' | dida task batch-create
```

#### task create / task update 完整参数

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | 项目名称或 ID (仅 create) |
| `--title` | `-t` | 标题 (仅 update) |
| `--content` | `-c` | 任务内容/备注 |
| `--desc` | | 描述 |
| `--tags` | | 标签 (逗号分隔) |
| `--all-day` | | 全天任务 |
| `--start-date` | `-s` | 开始日期 (today/tomorrow/YYYY-MM-DD/ISO) |
| `--due` | `-d` | 截止日期 (today/tomorrow/YYYY-MM-DD/ISO) |
| `--timezone` | | 时区 (默认 Asia/Shanghai) |
| `--reminders` | | 提醒 (逗号分隔, 如 TRIGGER:PT0S) |
| `--repeat` | | 重复规则 (RRULE) |
| `--priority` | `-p` | 优先级: none/low/medium/high |
| `--sort-order` | | 排序值 |
| `--items` | | 子任务 JSON |

### Projects

```bash
# 创建项目
dida project create "Shopping" --color "#F18181" --view-mode list

# 查看项目
dida project list                                 # 所有项目
dida project get "Work"                           # 项目详情及任务

# 更新项目
dida project update <project_id> --name "New Name" --color "#4A90D9"

# 删除项目
dida project delete <project_id>
```

#### project create / project update 参数

| Option | Short | Description |
|---|---|---|
| `--name` | `-n` | 项目名称 (仅 update) |
| `--color` | | 颜色 (如 #F18181) |
| `--view-mode` | | 视图模式: list/kanban/timeline |
| `--kind` | | 类型: TASK/NOTE |
| `--sort-order` | | 排序值 |

### JSON Output

All commands support `--json` for structured output:

```bash
dida task list --json
# {"success": true, "data": [...]}
```

### Version

```bash
dida --version
# dida 0.2.0
```

## Deprecated Commands

以下旧命令仍可使用但已弃用，请迁移到新命令：

| Old | New |
|---|---|
| `task add` | `task create` |
| `task done` | `task complete` |
| `task batch-add` | `task batch-create` |
| `project show` | `project get` |

## AI Agent Skill

安装 Skill 后，支持自然语言操作：

```
/dida365 show my work tasks
/dida365 create "Submit report" due tomorrow, high priority
/dida365 mark the report task as done
/dida365 what projects do I have
/dida365 create a project called "Q2 Goals"
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
4. **No Tag Management API** — API 不支持标签的独立管理，但任务可设置标签。
5. **No Habit Tracking** — API 不支持打卡/习惯功能。

## FAQ

**Q: 如何获取 Client ID 和 Client Secret?**
A: 前往 [developer.dida365.com](https://developer.dida365.com/) 注册应用，设置回调地址为 `http://localhost:18365/callback`。

**Q: `dida auth login` 打开浏览器后没有反应?**
A: 确保端口 18365 未被占用。

**Q: 可以用于 TickTick 国际版吗?**
A: 当前配置为 Dida365 (`api.dida365.com`)。使用国际版需修改 API 地址为 `api.ticktick.com`。
