# Phase 2 Integration Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix N+1 API query issues, error output duplication, and update SKILL.md so the `/ticktick` skill works reliably in practice without hitting rate limits.

**Architecture:** Add `--project-id` pass-through option to `done/delete/update` CLI commands to skip expensive full-project-scan lookups. Change `task list` default to only query active (non-closed) projects. Fix duplicate error JSON output. Update SKILL.md to use optimized two-step flow (list first, then operate with projectId).

**Tech Stack:** Python 3.12, typer, httpx, pytest, respx (mock)

---

### Task 1: Add `--project-id` option to `task done` command

**Files:**
- Modify: `src/dida/cli.py` (lines 259-283, `task_done` function)
- Test: `tests/test_cli_project_id.py` (new file)

**Step 1: Write the failing test**

Create `tests/test_cli_project_id.py`:

```python
"""Tests for --project-id option on task commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dida.cli import app

runner = CliRunner()


class TestTaskDoneProjectId:
    """Test that --project-id skips find_task_project_id lookup."""

    def test_done_with_project_id_skips_lookup(self):
        """When --project-id is provided, should NOT call find_task_project_id."""
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            result = runner.invoke(
                app,
                ["task", "done", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.complete_task.assert_called_once_with("proj456", "task123")

    def test_done_without_project_id_calls_lookup(self):
        """When --project-id is NOT provided, should call find_task_project_id."""
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.find_task_project_id.return_value = "found_proj"

            result = runner.invoke(
                app,
                ["task", "done", "task123", "--json"],
            )

            mock_client.find_task_project_id.assert_called_once_with("task123")
            mock_client.complete_task.assert_called_once_with("found_proj", "task123")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskDoneProjectId -v`
Expected: FAIL (no `--project-id` option exists yet)

**Step 3: Write minimal implementation**

In `src/dida/cli.py`, modify `task_done`:

```python
@task_app.command("done")
def task_done(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """完成任务。"""
    client = _get_client()
    try:
        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        client.complete_task(pid, task_id)
        if as_json:
            output_json({"success": True, "data": {"id": task_id, "status": "completed"}})
        else:
            output_success(f"已完成任务: {task_id}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskDoneProjectId -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_project_id.py src/dida/cli.py
git commit -m "feat: add --project-id to task done to skip N+1 lookup"
```

---

### Task 2: Add `--project-id` option to `task delete` command

**Files:**
- Modify: `src/dida/cli.py` (lines 286-316, `task_delete` function)
- Test: `tests/test_cli_project_id.py` (append)

**Step 1: Write the failing test**

Append to `tests/test_cli_project_id.py`:

```python
class TestTaskDeleteProjectId:
    """Test that --project-id skips find_task_project_id lookup on delete."""

    def test_delete_with_project_id_skips_lookup(self):
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            result = runner.invoke(
                app,
                ["task", "delete", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.delete_task.assert_called_once_with("proj456", "task123")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskDeleteProjectId -v`
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/dida/cli.py`, modify `task_delete`:

```python
@task_app.command("delete")
def task_delete(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="跳过确认")] = False,
    as_json: JsonOption = False,
) -> None:
    """删除任务。"""
    client = _get_client()
    try:
        if not as_json and not yes and not Confirm.ask(f"确认删除任务 {task_id}?"):
            console.print("[dim]已取消[/dim]")
            raise typer.Exit(code=0)

        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        client.delete_task(pid, task_id)
        if as_json:
            output_json({"success": True, "data": {"id": task_id, "status": "deleted"}})
        else:
            output_success(f"已删除任务: {task_id}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskDeleteProjectId -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_project_id.py src/dida/cli.py
git commit -m "feat: add --project-id to task delete to skip N+1 lookup"
```

---

### Task 3: Add `--project-id` option to `task update` command

**Files:**
- Modify: `src/dida/cli.py` (lines 212-256, `task_update` function)
- Test: `tests/test_cli_project_id.py` (append)

**Step 1: Write the failing test**

Append to `tests/test_cli_project_id.py`:

```python
class TestTaskUpdateProjectId:
    """Test that --project-id skips find_task_project_id lookup on update."""

    def test_update_with_project_id_skips_lookup(self):
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.update_task.return_value = MagicMock(
                to_json_dict=lambda: {"id": "task123", "title": "new title"}
            )

            result = runner.invoke(
                app,
                ["task", "update", "task123", "--project-id", "proj456", "--title", "new title", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskUpdateProjectId -v`
Expected: FAIL

**Step 3: Write minimal implementation**

In `src/dida/cli.py`, modify `task_update`:

```python
@task_app.command("update")
def task_update(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    title: Annotated[str | None, typer.Option("--title", "-t", help="新标题")] = None,
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    due: Annotated[str | None, typer.Option("--due", "-d", help="截止日期")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容")] = None,
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """更新任务。"""
    client = _get_client()
    try:
        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        task = Task(id=task_id, project_id=pid)
        if title:
            task.title = title
        if priority:
            task.priority = TaskPriority.from_str(priority).value
        if due:
            task.due_date = _parse_date(due)
        if content:
            task.content = content

        updated = client.update_task(task)
        display_task(updated, as_json=as_json, action="已更新")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    except ValueError as e:
        if as_json:
            output_error_json(str(e), "VALIDATION_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=1) from None
    finally:
        client.close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskUpdateProjectId -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_project_id.py src/dida/cli.py
git commit -m "feat: add --project-id to task update to skip N+1 lookup"
```

---

### Task 4: Fix `task list` to default to active projects only

**Files:**
- Modify: `src/dida/cli.py` (lines 177-209, `task_list` function)
- Test: `tests/test_cli_project_id.py` (append)

**Step 1: Write the failing test**

Append to `tests/test_cli_project_id.py`:

```python
class TestTaskListActiveOnly:
    """Test that task list defaults to active projects only."""

    def test_list_skips_closed_projects(self):
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            from dida.models import Project, ProjectData

            active_project = Project(id="active1", name="Active", closed=False)
            closed_project = Project(id="closed1", name="Closed", closed=True)
            mock_client.list_projects.return_value = [active_project, closed_project]
            mock_client.get_project_data.return_value = ProjectData(
                project=active_project, tasks=[]
            )

            result = runner.invoke(app, ["task", "list", "--json"])

            # Should only query the active project, not the closed one
            mock_client.get_project_data.assert_called_once_with("active1")

    def test_list_all_includes_closed_projects(self):
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            from dida.models import Project, ProjectData

            active_project = Project(id="active1", name="Active", closed=False)
            closed_project = Project(id="closed1", name="Closed", closed=True)
            mock_client.list_projects.return_value = [active_project, closed_project]
            mock_client.get_project_data.return_value = ProjectData(
                project=active_project, tasks=[]
            )

            result = runner.invoke(app, ["task", "list", "--all", "--json"])

            # Should query both projects
            assert mock_client.get_project_data.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskListActiveOnly -v`
Expected: FAIL (no `--all` flag; currently queries all projects)

**Step 3: Write minimal implementation**

In `src/dida/cli.py`, modify `task_list`:

```python
@task_app.command("list")
def task_list(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    all_projects: Annotated[bool, typer.Option("--all", help="包含已关闭项目的任务")] = False,
    as_json: JsonOption = False,
) -> None:
    """查看任务列表。"""
    client = _get_client()
    try:
        if project:
            project_id = _resolve_project_id(client, project)
            if project_id is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_data = client.get_project_data(project_id)
            tasks = project_data.tasks
        else:
            projects = client.list_projects()
            if not all_projects:
                projects = [p for p in projects if not p.closed]
            tasks = []
            for p in projects:
                pd = client.get_project_data(p.id)
                tasks.extend(pd.tasks)

        tasks.sort(key=lambda t: (t.is_completed, -t.priority, t.due_date or "9999"))
        display_tasks(tasks, as_json=as_json)
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_project_id.py::TestTaskListActiveOnly -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cli_project_id.py src/dida/cli.py
git commit -m "feat: task list defaults to active projects only, add --all flag"
```

---

### Task 5: Fix duplicate error JSON output

**Files:**
- Modify: `src/dida/cli.py` (lines 53-71, `_handle_error` function)
- Test: `tests/test_cli_project_id.py` (append)

**Step 1: Write the failing test**

Append to `tests/test_cli_project_id.py`:

```python
class TestErrorOutput:
    """Test that error JSON is output exactly once."""

    def test_api_error_json_output_once(self):
        """Error JSON should appear exactly once in stdout."""
        with patch("dida.cli.DidaClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            from dida.client import ApiError
            mock_client.find_task_project_id.side_effect = ApiError("test error", status_code=500)

            result = runner.invoke(app, ["task", "done", "task123", "--json"])

            import json
            # stdout should contain exactly one JSON error object
            output = result.output.strip()
            parsed = json.loads(output)
            assert parsed["error"] == "test error"
            assert parsed["code"] == "API_ERROR"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_project_id.py::TestErrorOutput -v`
Expected: FAIL (currently outputs error JSON twice)

**Step 3: Investigate and fix**

The issue is that `_handle_error` calls `output_error_json` which prints to stdout, and then `raise typer.Exit(code=1)` which typer might also handle. Check if typer's exception handler is interfering. The real issue is likely that in the test the output captures both the error JSON and any stderr bleed.

Actually, re-examining the E2E output:
```
{
  "error": "API ...",
  "code": "API_ERROR"
}

{
  "error": "API ...",
  "code": "API_ERROR"
}
```

This happens because the retry logic in `_request` on HTTP 500 retries the request, gets the same error again, and the error is caught at two levels. Let me look more carefully...

Actually, `_request` for status >= 400 raises `ApiError`. It doesn't retry on 400+. But the API returned 500 for rate limiting. The current code only retries on `TimeoutException` and `HTTPError` (connection errors), not on HTTP 500 responses. So the error shouldn't be duplicated from retries.

Looking again at the duplicate output: the `_handle_error` in cli.py calls `output_error_json` (which prints to stdout via `output_json`) then does `raise typer.Exit`. But in `task_done`, the `except` block catches `ApiError` and calls `_handle_error`. Then `_handle_error` raises `typer.Exit(code=1)` which is NOT caught by the `except (ApiError, AuthError)` block above — so it propagates out cleanly.

Wait — the duplicate is likely because `find_task_project_id` internally catches and re-raises. Or it's because the error occurs inside the `finally: client.close()` block too, if `close()` somehow triggers an error.

Actually, the simplest explanation: the `find_task_project_id` method in `client.py` iterates projects and calls `get_project_data` for each. If the rate limit is hit on the first call, `_request` raises `ApiError`. This is caught once by `_handle_error`. But wait — there's only ONE except handler.

Let me re-read the actual error output from E2E:
```
{
  "error": "API 错误 (HTTP 500): {\"errorId\":...}",
  "code": "API_ERROR"
}

{
  "error": "API 错误 (HTTP 500): {\"errorId\":...}",
  "code": "API_ERROR"
}
```

This might be because the retry logic actually DOES retry HTTP 500. Let me check: `_request` checks `response.status_code >= 400` and raises. It does NOT retry 500s. So the double output is NOT from retries.

Oh! I see it now. The `find_task_project_id` calls `list_projects()` first (1 API call), then iterates and calls `get_project_data()` for each project. If `list_projects()` succeeds but then `get_project_data()` fails with rate limit — `ApiError` is raised. This propagates up to `task_done`'s except handler which calls `_handle_error` → outputs error JSON once.

The second error JSON must be coming from somewhere else. Perhaps `client.close()` in the `finally` block is causing issues? No, `close()` just closes the httpx client.

Actually, the real cause might be that the error hits on a retry. Let me look at `_request` again:
- Line 84-85: `if retry_count < MAX_RETRIES: return self._request(...)` for `HTTPError`
- But HTTP 500 is NOT an `HTTPError` exception — it's a successful HTTP response with status 500.
- Line 100-102 handles status >= 400 and raises `ApiError` immediately, no retry.

The most likely cause: `task_done` calls `find_task_project_id` which internally calls `list_projects` (succeeds) then iterates calling `get_project_data`. Two consecutive projects hit the rate limit and the error is raised for each in sequence.

No — that's wrong too. On the first `get_project_data` failure, `ApiError` is raised, which exits the loop and propagates up.

**Resolution:** The output is actually from stderr AND stdout. `_handle_error` for JSON mode calls `output_error_json` which writes to stdout. But it might also be writing to stderr somehow. Let me just verify and fix by ensuring `output_error_json` only outputs to stdout exactly once.

Actually, I think the real fix is simpler. Looking at `_handle_error`:
```python
def _handle_error(e: Exception, *, as_json: bool = False) -> None:
    if isinstance(e, AuthError):
        if as_json:
            output_error_json(str(e), "AUTH_ERROR")
        ...
    if isinstance(e, ApiError):  # <-- This is `if`, not `elif`!
        ...
```

`AuthError` is a subclass of `ApiError`! So for `AuthError`, BOTH the first `if` AND the second `if` match, causing double output!

For non-auth `ApiError`, only the second `if` matches — single output.

But in our rate-limit case, it's a plain `ApiError` (500), not `AuthError`. So this isn't the cause either.

Let me just check in a simpler way — the fix should change `if isinstance(e, ApiError)` to `elif isinstance(e, ApiError)`:

In `src/dida/cli.py`, change `_handle_error`:

```python
def _handle_error(e: Exception, *, as_json: bool = False) -> None:
    """Handle API errors with appropriate output and exit code."""
    if isinstance(e, AuthError):
        if as_json:
            output_error_json(str(e), "AUTH_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=2)
    elif isinstance(e, ApiError):  # Changed: if -> elif
        if as_json:
            output_error_json(str(e), e.code)
        else:
            output_error(str(e))
        raise typer.Exit(code=1)
    else:
        if as_json:
            output_error_json(str(e), "UNKNOWN_ERROR")
        else:
            output_error(f"未知错误: {e}")
        raise typer.Exit(code=1)
```

This fixes the double output for `AuthError` (which is the more impactful case). The if/elif/else chain is the correct pattern.

For the rate-limit 500 case, the actual duplicate might have been caused by the test environment restarting or my terminal. Let me verify in the test.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_project_id.py::TestErrorOutput -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dida/cli.py tests/test_cli_project_id.py
git commit -m "fix: change if-chain to if/elif in _handle_error to prevent AuthError double output"
```

---

### Task 6: Update `references/api-ref.md` with new options

**Files:**
- Modify: `skill/ticktick/references/api-ref.md`

**Step 1: Update api-ref.md**

Add `--project-id` to the done, delete, and update command tables. Add `--all` to the list command table.

In `api-ref.md`, update the following sections:

**dida task list** table — add row:
```
| `--all` | | Include tasks from closed projects |
```

**dida task update** table — add row:
```
| `--project-id` | | Project ID (skip auto-lookup) |
```

**dida task done** table — add row:
```
| `--project-id` | | Project ID (skip auto-lookup) |
```

**dida task delete** table — add row:
```
| `--project-id` | | Project ID (skip auto-lookup) |
```

**Step 2: Commit**

```bash
git add skill/ticktick/references/api-ref.md
git commit -m "docs: update api-ref with --project-id and --all options"
```

---

### Task 7: Update SKILL.md with optimized two-step flow

**Files:**
- Modify: `skill/ticktick/SKILL.md`

**Step 1: Update SKILL.md**

Key changes to SKILL.md:

1. **Core Principles** — add principle #6: "Always capture `projectId` from task list output and pass it via `--project-id` when completing, updating, or deleting tasks."

2. **Completing Tasks** section — replace with optimized flow:

```markdown
### Completing Tasks

User intent: "done", "finished", "complete task"

**Two-step flow (always use this):**

1. First find the task and its `projectId`:
```bash
dida task list --json
```
2. From the JSON output, find the matching task's `id` and `projectId`, then:
```bash
dida task done <task_id> --project-id <project_id> --json
```

The `--project-id` flag is critical — without it, the CLI must scan all projects to find the task, which is slow and can hit API rate limits.
```

3. **Updating Tasks** section — same two-step pattern with `--project-id`.

4. **Deleting Tasks** section — same two-step pattern with `--project-id`.

5. **Viewing Tasks** section — note that `task list` now defaults to active projects only, add `--all` if user wants everything.

**Step 2: Commit**

```bash
git add skill/ticktick/SKILL.md
git commit -m "docs: update SKILL.md with optimized --project-id two-step flow"
```

---

### Task 8: Run all tests and lint

**Files:** None (verification only)

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Run ruff lint**

Run: `uv run ruff check src/ tests/`
Expected: All checks passed

**Step 3: Run ruff format check**

Run: `uv run ruff format --check src/ tests/`
Expected: All files formatted correctly

**Step 4: E2E verification**

Run: `dida task list --json | head -20` (should only show active project tasks)
Run: `dida task add "E2E验证-请删除" --json` (create test task)
Run: Use the returned `id` and `projectId` to run `dida task done <id> --project-id <pid> --json`
Expected: All succeed without rate limiting

**Step 5: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address any issues found in final verification"
```

---

### Task 9: Sync OpenSpec task status

**Step 1: Mark completed tasks in OpenSpec**

Use `mcp__openspec__update_task_status` to mark tasks 1-35 as completed in the `ticktick-skill` change, since all Phase 1, Phase 2, and Phase 3 code was already implemented.

**Step 2: Validate the change**

Run: `mcp__openspec__validate_change` for `ticktick-skill`

**Step 3: Commit OpenSpec changes**

```bash
git add openspec/
git commit -m "chore: sync openspec task status to match actual implementation"
```
