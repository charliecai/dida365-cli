# Project-Management Specification

## Purpose

通过 `dida project` CLI 命令查看和管理项目（清单），为任务操作提供项目上下文。支持项目名称模糊匹配，方便 CLI 和 Skill 使用。

## Requirements

### Requirement: 查看所有项目

**User Story:** As a user, I want to see all my TickTick projects.

#### Acceptance Criteria

1. WHEN user runs `dida project list` THEN system SHALL call `GET /open/v1/project`
2. system SHALL display: project name, ID
3. system SHALL use rich table for terminal output
4. WHEN `--json` is used THEN system SHALL output JSON array of projects

#### Scenario: CLI List Projects

1. User runs `dida project list`
2. System calls API, receives project list
3. System displays formatted table with project names and IDs

#### Scenario: Skill List Projects

1. User says "/ticktick 我有哪些项目"
2. Claude runs `dida project list --json`
3. Claude formats JSON into readable response

### Requirement: 查看项目详情与任务

**User Story:** As a user, I want to view all tasks within a specific project.

#### Acceptance Criteria

1. WHEN user runs `dida project show <name-or-id>` THEN system SHALL display project info and all tasks
2. WHEN input is project name THEN system SHALL resolve name to ID via project list (fuzzy match)
3. WHEN `--json` is used THEN system SHALL output structured JSON with project info and tasks array
4. IF project not found THEN system SHALL display available projects for user to choose

#### Scenario: View Project by Name

1. User runs `dida project show 工作`
2. System calls `GET /open/v1/project` to resolve "工作" → project ID
3. System calls `GET /open/v1/project/{id}/data`
4. System displays project name and tasks with status, priority, due dates

### Requirement: 项目名称模糊匹配

**User Story:** As a user, I want to reference projects by approximate names.

#### Acceptance Criteria

1. WHEN user references a project by name THEN system SHALL perform case-insensitive substring matching
2. IF multiple projects match THEN system SHALL present matches for user to choose (interactive) or return all matches (JSON)
3. IF no project matches THEN system SHALL list all available projects
