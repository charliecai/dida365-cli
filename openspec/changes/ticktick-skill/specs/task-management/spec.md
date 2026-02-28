# Task-Management Specification

## Purpose

通过 `dida task` CLI 命令实现任务的完整生命周期管理。CLI 层封装 Open API v1 调用，Skill 层通过调用 CLI 命令实现自然语言交互。

## Requirements

### Requirement: 创建任务

**User Story:** As a user, I want to create tasks via CLI or natural language.

#### Acceptance Criteria

1. WHEN user runs `dida task add <title>` THEN system SHALL call `POST /open/v1/task`
2. WHEN `--project` is not specified THEN system SHALL create task in inbox (project_id="")
3. WHEN `--priority` is specified THEN system SHALL accept: none, low, medium, high and map to API values 0, 1, 3, 5
4. WHEN `--due` is specified THEN system SHALL parse natural date expressions (e.g., "tomorrow", "2026-03-01") and format as ISO 8601
5. WHEN `--content` is specified THEN system SHALL set task content/notes
6. WHEN task is created successfully THEN system SHALL display task title, project, and ID

#### Scenario: CLI Create Task

1. User runs `dida task add "提交报告" --priority high --due tomorrow`
2. System parses: title="提交报告", priority=5, due_date=2026-03-01
3. System calls API and receives created task
4. System displays "已创建: 提交报告 [高优先级] 截止: 2026-03-01"

#### Scenario: Skill Create Task

1. User says "/ticktick 创建任务：明天下午3点前提交报告，高优先级"
2. Claude parses intent and runs `dida task add "提交报告" --priority high --due "2026-03-01T15:00" --json`
3. Claude reads JSON output and confirms to user

### Requirement: 查看任务

**User Story:** As a user, I want to view my tasks from a project or inbox.

#### Acceptance Criteria

1. WHEN user runs `dida task list` THEN system SHALL list inbox tasks
2. WHEN `--project <name>` is specified THEN system SHALL resolve project name to ID and list project tasks
3. system SHALL display: title, priority, due date, status
4. WHEN `--json` is used THEN system SHALL output structured JSON array
5. system SHALL use rich table for terminal output with color-coded priorities

### Requirement: 更新任务

**User Story:** As a user, I want to update existing tasks.

#### Acceptance Criteria

1. WHEN user runs `dida task update <id>` with update flags THEN system SHALL call `POST /open/v1/task/{id}`
2. Supported flags: `--title`, `--content`, `--priority`, `--due`, `--project`
3. system SHALL only send changed fields plus required `id` and `projectId`
4. WHEN update succeeds THEN system SHALL confirm changes

### Requirement: 完成任务

**User Story:** As a user, I want to mark tasks as complete.

#### Acceptance Criteria

1. WHEN user runs `dida task done <id>` THEN system SHALL resolve project ID and call `POST /open/v1/project/{pid}/task/{tid}/complete`
2. WHEN completed successfully THEN system SHALL display "已完成: <task title>"
3. IF task not found THEN system SHALL exit with error code 1

### Requirement: 删除任务

**User Story:** As a user, I want to delete tasks.

#### Acceptance Criteria

1. WHEN user runs `dida task delete <id>` THEN system SHALL resolve project ID and call `DELETE /open/v1/task/{pid}/{tid}`
2. WHEN `--yes` flag is NOT provided THEN system SHALL prompt confirmation
3. WHEN `--json` mode is used THEN system SHALL skip confirmation (for Skill use)
4. WHEN deleted THEN system SHALL display "已删除: <task title>"

### Requirement: 批量创建任务

**User Story:** As a user, I want to create multiple tasks at once.

#### Acceptance Criteria

1. WHEN user runs `dida task batch-add` with stdin JSON THEN system SHALL call `POST /open/v1/batch/task`
2. WHEN batch succeeds THEN system SHALL display count and summary
3. IF partial failure THEN system SHALL report which tasks succeeded and failed

## Data Model

### Task Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | read-only | Task ID |
| projectId | string | create: optional | Project ID, empty for inbox |
| title | string | yes | Task title |
| content | string | no | Task content/notes |
| desc | string | no | Task description |
| allDay | boolean | no | All-day task flag |
| startDate | string | no | ISO 8601 datetime |
| dueDate | string | no | ISO 8601 datetime |
| timeZone | string | no | e.g. "Asia/Shanghai" |
| reminders | string[] | no | RFC 5545 TRIGGER format |
| repeat | string | no | RRULE format |
| priority | int | no | 0=none, 1=low, 3=medium, 5=high |
| status | int | read-only | 0=normal, 2=completed |
| items | object[] | no | Subtasks/checklist items |
