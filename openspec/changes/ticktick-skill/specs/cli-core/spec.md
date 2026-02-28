# CLI-Core Specification

## Purpose

提供独立可用的 Python CLI 工具 (`dida`)，作为整个项目的核心层。CLI 封装滴答清单 Open API v1，提供结构化的命令行接口，同时支持 `--json` 输出以便上层 Skill 解析。

## Requirements

### Requirement: CLI 项目结构

**User Story:** As a developer, I want the CLI to follow standard Python project conventions so it's easy to install and maintain.

#### Acceptance Criteria

1. system SHALL use `src/dida/` 作为包目录布局
2. system SHALL use `pyproject.toml` 管理依赖和构建配置
3. system SHALL use UV 作为包管理器
4. system SHALL 通过 `[project.scripts]` 注册 `dida` 命令入口
5. system SHALL 使用 ruff 进行代码格式化和 lint
6. 核心依赖 SHALL 仅包含: typer, httpx, rich (终端美化)

### Requirement: CLI 命令结构

**User Story:** As a user, I want intuitive CLI commands to manage my TickTick tasks and projects.

#### Acceptance Criteria

1. system SHALL 使用 typer 作为 CLI 框架
2. system SHALL 提供以下命令组:
   - `dida auth` — 认证相关 (login, status, logout)
   - `dida task` — 任务管理 (add, list, update, done, delete, batch-add)
   - `dida project` — 项目管理 (list, show)
3. 每个命令 SHALL 支持 `--help` 显示用法说明
4. 所有列表类命令 SHALL 支持 `--json` 输出 JSON 格式
5. system SHALL 使用 rich 美化终端输出（表格、颜色、图标）

#### Scenario: CLI Help

1. User runs `dida --help`
2. System displays available command groups: auth, task, project
3. User runs `dida task --help`
4. System displays task subcommands: add, list, update, done, delete, batch-add

### Requirement: JSON 输出模式

**User Story:** As a Skill developer, I want CLI to output structured JSON so Claude can reliably parse the results.

#### Acceptance Criteria

1. WHEN `--json` flag is provided THEN system SHALL output valid JSON to stdout
2. JSON 输出 SHALL 不包含 ANSI 颜色码或装饰字符
3. 错误信息在 JSON 模式下 SHALL 输出为 `{"error": "message", "code": "ERROR_CODE"}`
4. 成功响应 SHALL 包含 `{"success": true, "data": {...}}`

### Requirement: 错误处理与退出码

**User Story:** As a user, I want clear error messages when something goes wrong.

#### Acceptance Criteria

1. system SHALL 使用标准退出码: 0=成功, 1=通用错误, 2=认证错误, 3=网络错误
2. 所有错误 SHALL 输出到 stderr，不混入 stdout
3. API 错误 SHALL 翻译为用户友好的中文提示
4. 网络超时 SHALL 提示 "网络请求超时，请检查网络连接后重试"
