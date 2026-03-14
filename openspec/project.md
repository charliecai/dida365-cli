# Project Context

## Overview

Dida365 CLI + Skill — 分层架构项目。底层是一个独立可用的 Python CLI 工具（`dida`），用于通过命令行操作滴答清单 (Dida365)。上层是一个 Claude Code Skill（`/dida365`），通过调用 CLI 实现自然语言操作任务。

## Tech Stack

- **语言**: Python 3.12+
- **包管理**: UV
- **CLI 框架**: typer
- **HTTP 客户端**: httpx
- **API**: 滴答清单 Open API v1 (`https://api.dida365.com/open/v1`)
- **认证**: OAuth 2.0 Bearer Token
- **Skill 格式**: Claude Code Skill (SKILL.md)
- **格式化/Lint**: ruff

## Conventions

- 分层架构：CLI 核心库 → Skill 薄封装
- CLI 输出支持 `--json` 格式，方便 Skill 解析
- Python 代码遵循 PEP 8，使用 ruff 格式化
- 所有 API 调用包含错误处理和超时控制
- 敏感信息（Token）存储在 `~/.dida365/`，不硬编码
- Skill 目录结构遵循 Claude Code Agent Skills 开放标准

## Architecture

```
项目根目录 (dida365-cli/)
├── src/
│   └── dida/                 # CLI 核心库（Python 包）
│       ├── __init__.py
│       ├── cli.py            # typer CLI 入口
│       ├── client.py         # API 客户端封装
│       ├── auth.py           # OAuth 认证
│       └── models.py         # 数据模型
├── tests/                    # 测试
├── pyproject.toml            # 项目配置 (uv)
└── skill/                    # Claude Code Skill
    └── dida365/
        ├── SKILL.md          # Skill 定义与指令
        └── references/
            └── api-ref.md    # API 速查

安装后:
  - CLI: `dida` 命令全局可用
  - Skill: 软链接或复制 skill/dida365/ → ~/.claude/skills/dida365/
```

## Development Workflow

1. 使用 OpenSpec 管理需求与任务
2. 遵�� Conventional Commits
3. Phase 1: CLI 核心库开发 → 独立可用
4. Phase 2: Skill 封装 → 调用 CLI 实现自然语言交互
