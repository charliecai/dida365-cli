# Tasks

## Phase 1: CLI 核心库 (`dida`)

### 1.1 项目初始化

- [ ] 初始化 Python 项目: pyproject.toml, src/dida/ 目录结构
- [ ] 配置 UV 依赖管理, 添加核心依赖 (typer, httpx, rich)
- [ ] 配置 ruff 格式化与 lint
- [ ] 配置 pytest 测试框架

### 1.2 数据模型与 API 客户端

- [ ] 实现数据模型 (models.py): Task, Project, TaskPriority 等
- [ ] 实现 httpx HTTP 客户端封装 (client.py)
- [ ] 封装所有 Open API v1 端点方法
- [ ] 实现错误处理、超时(30s)、重试(3次)
- [ ] 实现 `--json` 输出支持 (JSON 与 rich 双模式)
- [ ] 编写 API 客户端单元测试 (mock httpx)

### 1.3 OAuth 认证

- [ ] 实现 OAuth 2.0 授权流程 (auth.py): 浏览器授权 + 本地回调
- [ ] 实现 Token 安全存储 (~/.config/ticktick/token.json, 权限 0600)
- [ ] 实现 Token 有效性检查与自动刷新
- [ ] 实现 `dida auth` CLI 命令组 (login, status, logout)
- [ ] 编写认证模块单元测试

### 1.4 任务管理 CLI

- [ ] 实现 `dida task add` — 创建任务 (含 --priority, --due, --project, --content)
- [ ] 实现 `dida task list` — 查看任务 (含 --project, --json)
- [ ] 实现 `dida task update` — 更新任务
- [ ] 实现 `dida task done` — 完成任务
- [ ] 实现 `dida task delete` — 删除任务 (含 --yes 跳过确认)
- [ ] 实现 `dida task batch-add` — 批量创建 (stdin JSON)

### 1.5 项目管理 CLI

- [ ] 实现 `dida project list` — 查看项目列表
- [ ] 实现 `dida project show` — 查看项目详情及任务
- [ ] 实现项目名称模糊匹配

### 1.6 Phase 1 测试与验证

- [ ] 编写核心功能集成测试
- [ ] 手动端到端测试 (实际 API 调用)
- [ ] 边界情况测试 (无效 Token、网络超时、空项目等)

## Phase 2: Claude Code Skill (`/ticktick`)

### 2.1 SKILL.md 编写

- [ ] 编写 SKILL.md frontmatter (name, description, disable-model-invocation)
- [ ] 编写 Skill 核心指令: 如何将用户自然语言意图映射到 `dida` CLI 命令
- [ ] 编写常见使用示例 (create, list, done, delete)

### 2.2 参考文档

- [ ] 编写 references/api-ref.md — CLI 命令速查表

### 2.3 安装与集成

- [ ] 实现安装脚本: 软链接 skill/ → ~/.claude/skills/ticktick/
- [ ] 端到端测试: 通过 `/ticktick` 调用 Claude 验证各功能

## Phase 3: 文档

- [ ] 编写 README.md (项目说明、安装配置、使用方法)
- [ ] 记录已知限制与 FAQ
