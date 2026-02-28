# ticktick-skill

## Why

当前使用滴答清单管理任务时，需要频繁切换到滴答清单 App 或网页端操作。作为 Claude Code 的重度用户，希望能在 Claude Code 中直接通过自然语言管理任务，实现"对话即操作"的工作流，减少上下文切换，提升效率。

## What

采用分层架构，分两个阶段交付：

### Phase 1: CLI 核心库 (`dida`)

独立可用的 Python CLI 工具，通过滴答清单 Open API v1 管理任务：

1. **任务管理** — 创建、查看、更新、删除、完成任务
2. **项目管理** — 查看项目列表、查看项目下的任务
3. **OAuth 认证** — 安全管理 Access Token

CLI 命令示例：
```
dida auth login              # OAuth 认证
dida task add "买牛奶" -p high  # 创建任务
dida task list                # 查看任务
dida task done <id>           # 完成任务
dida project list             # 查看项目
```

### Phase 2: Claude Code Skill (`/ticktick`)

薄封装层，通过 SKILL.md 指引 Claude 调用 `dida` CLI 完成自然语言操作。

### 不包含（Non-Goals）

- 习惯打卡功能（官方 Open API 不支持）
- 标签管理（官方 Open API 不支持）
- Webhook / 实时推送
- 多用户协作功能

## How

### 技术方案

- **分层架构**: CLI 核心库（`dida`）+ Skill 薄封装（`/ticktick`）
- **CLI 框架**: typer（类型安全、自动补全、帮助文档）
- **API 客户端**: httpx 封装，调用 `https://api.dida365.com/open/v1`
- **输出格式**: 默认人类可读，`--json` 输出结构化 JSON（方便 Skill 解析）
- **认证方式**: OAuth 2.0 Bearer Token，Token 存储在 `~/.config/ticktick/token.json`
- **错误处理**: 所有 API 调用包含超时（30s）、重试（最多 3 次）、友好错误提示
- **Skill 形态**: SKILL.md 指引 Claude 通过 Bash 调用 `dida` 命令

### API 端点映射

| CLI 命令 | HTTP 方法 | 端点 |
|----------|----------|------|
| `dida project list` | GET | `/project` |
| `dida project show <id>` | GET | `/project/{id}/data` |
| `dida task add <title>` | POST | `/task` |
| `dida task update <id>` | POST | `/task/{id}` |
| `dida task done <id>` | POST | `/project/{pid}/task/{tid}/complete` |
| `dida task delete <id>` | DELETE | `/task/{pid}/{tid}` |
| `dida task batch-add` | POST | `/batch/task` |

## Impact

- **用户体验**: CLI 独立可用 + Skill 自然语言交互，两种使用方式
- **可扩展性**: CLI 核心库可以未来包装为 MCP Server
- **安全性**: Token 本地存储，不传输到第三方服务
- **依赖**: 需要用户在滴答清单开发者平台注册应用获取 Client ID/Secret
- **风险**: 官方 API 仍处于 Beta 阶段，接口可能变更
