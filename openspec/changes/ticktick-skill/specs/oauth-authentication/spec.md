# OAuth-Authentication Specification

## Purpose

管理滴答清单 API 的 OAuth 2.0 认证流程，安全地获取、存储和刷新 Access Token。通过 `dida auth` CLI 命令提供认证操作，确保所有 API 调用都能通过认证。

## Requirements

### Requirement: Token 初始化

**User Story:** As a user, I want to set up my TickTick API credentials via CLI so that the tool can access my TickTick account.

#### Acceptance Criteria

1. WHEN user runs `dida auth login` THEN system SHALL prompt for Client ID and Client Secret
2. WHEN user provides credentials THEN system SHALL open browser for OAuth authorization at `https://dida365.com/oauth/authorize`
3. system SHALL start local HTTP server to receive OAuth callback with authorization code
4. WHEN code is received THEN system SHALL exchange for access token via `https://dida365.com/oauth/token`
5. WHEN token is obtained THEN system SHALL store token securely at `~/.config/ticktick/token.json`
6. IF credentials are invalid THEN system SHALL display clear error message and retry instructions

#### Scenario: First-time Setup via CLI

1. User runs `dida auth login`
2. System prompts: "请输入 Client ID:"
3. User enters Client ID
4. System prompts: "请输入 Client Secret:"
5. User enters Client Secret
6. System opens browser for authorization, starts local callback server
7. User authorizes in browser, browser redirects to localhost callback
8. System receives code, exchanges for token
9. System saves token and displays "认证成功"

#### Scenario: First-time Setup via Skill

1. User invokes `/ticktick 查看任务`
2. Claude runs `dida auth status --json`, detects no token
3. Claude prompts user: "请先运行 `dida auth login` 完成认证"

### Requirement: 认证状态查询

**User Story:** As a user, I want to check if my authentication is still valid.

#### Acceptance Criteria

1. WHEN user runs `dida auth status` THEN system SHALL display token validity and expiry
2. WHEN `--json` is used THEN system SHALL output `{"authenticated": true/false, "expires_at": "..."}`
3. IF no token exists THEN system SHALL display "未认证，请运行 dida auth login"

### Requirement: Token 存储安全

**User Story:** As a user, I want my API credentials to be stored securely and never exposed in code or logs.

#### Acceptance Criteria

1. WHEN token is stored THEN system SHALL save to `~/.config/ticktick/token.json` with file permission `0600`
2. system SHALL NOT log or print token values to stdout/stderr
3. system SHALL NOT hardcode any credentials in source code
4. WHEN token file exists THEN system SHALL read from it for all API calls

### Requirement: Token 有效性检查与刷新

**User Story:** As a user, I want the tool to handle expired tokens gracefully without manual intervention.

#### Acceptance Criteria

1. WHEN API returns 401 Unauthorized THEN system SHALL attempt to refresh the token
2. IF refresh fails THEN system SHALL exit with code 2 and prompt user to run `dida auth login`
3. WHEN making API calls THEN system SHALL include `Authorization: Bearer {token}` header

### Requirement: 登出

**User Story:** As a user, I want to remove my stored credentials.

#### Acceptance Criteria

1. WHEN user runs `dida auth logout` THEN system SHALL delete `~/.config/ticktick/token.json`
2. system SHALL confirm "已登出，Token 已删除"
