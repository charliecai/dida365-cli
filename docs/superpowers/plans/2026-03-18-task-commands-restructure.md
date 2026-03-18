# Task Commands Restructure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `task list`, add `task move`/`task filter`/`task completed` commands, bump version to 0.3.0.

**Architecture:** Each new command follows the existing pattern: CLI function (typer) → client method (httpx) → API endpoint. All three new endpoints use POST with JSON body. Tests use respx for client and MagicMock for CLI.

**Tech Stack:** Python 3.12, typer, httpx, respx, pytest, rich

---

### Task 1: Add client methods for move/filter/completed

**Files:**
- Modify: `src/dida/client.py` (add 3 methods after `batch_create_tasks`)
- Test: `tests/test_client.py` (add 3 test methods)

- [ ] **Step 1: Write failing tests for the three new client methods**

Add to `tests/test_client.py` inside `TestDidaClient`:

```python
    @respx.mock
    def test_move_task(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/move").mock(
            return_value=httpx.Response(
                200,
                json=[{"taskId": "t1", "etag": "abc123"}],
            )
        )
        result = client.move_task("t1", "p_from", "p_to")
        assert result == [{"taskId": "t1", "etag": "abc123"}]

    @respx.mock
    def test_filter_tasks(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "t1", "title": "Task 1", "projectId": "p1"},
                    {"id": "t2", "title": "Task 2", "projectId": "p1"},
                ],
            )
        )
        tasks = client.filter_tasks(project_ids=["p1"], priority=[5])
        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"

    @respx.mock
    def test_filter_tasks_empty(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(200, json=[])
        )
        tasks = client.filter_tasks()
        assert tasks == []

    @respx.mock
    def test_list_completed_tasks(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "t3", "title": "Done task", "status": 2, "projectId": "p1",
                     "completedTime": "2026-03-15T10:00:00+0000"},
                ],
            )
        )
        tasks = client.list_completed_tasks(project_ids=["p1"])
        assert len(tasks) == 1
        assert tasks[0].status == 2

    @respx.mock
    def test_list_completed_tasks_empty(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(200, json=[])
        )
        tasks = client.list_completed_tasks()
        assert tasks == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_client.py::TestDidaClient::test_move_task tests/test_client.py::TestDidaClient::test_filter_tasks tests/test_client.py::TestDidaClient::test_list_completed_tasks -v`
Expected: FAIL with `AttributeError: 'DidaClient' object has no attribute 'move_task'`

- [ ] **Step 3: Implement the three client methods**

Add to `src/dida/client.py` in `DidaClient` class, after `batch_create_tasks`:

```python
    def move_task(
        self,
        task_id: str,
        from_project_id: str,
        to_project_id: str,
    ) -> list[dict]:
        """Move a task between projects. POST /task/move"""
        payload = [
            {
                "taskId": task_id,
                "fromProjectId": from_project_id,
                "toProjectId": to_project_id,
            }
        ]
        data = self._request("POST", "/task/move", json=payload)
        return data if isinstance(data, list) else []

    def filter_tasks(
        self,
        *,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        priority: list[int] | None = None,
        tags: list[str] | None = None,
        status: list[int] | None = None,
    ) -> list[Task]:
        """Filter tasks. POST /task/filter"""
        payload: dict = {}
        if project_ids:
            payload["projectIds"] = project_ids
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if priority:
            # API field is misspelled as "proiority"
            payload["proiority"] = priority
        if tags:
            payload["tag"] = tags
        if status:
            payload["status"] = status
        data = self._request("POST", "/task/filter", json=payload)
        if isinstance(data, list):
            return [Task.from_dict(t) for t in data]
        return []

    def list_completed_tasks(
        self,
        *,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Task]:
        """List completed tasks. POST /task/completed"""
        payload: dict = {}
        if project_ids:
            payload["projectIds"] = project_ids
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        data = self._request("POST", "/task/completed", json=payload)
        if isinstance(data, list):
            return [Task.from_dict(t) for t in data]
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_client.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/dida/client.py tests/test_client.py
git commit -m "feat: add move_task, filter_tasks, list_completed_tasks client methods"
```

---

### Task 2: Remove `task list` command and its tests

**Files:**
- Modify: `src/dida/cli.py` (delete `task_list` function, lines 355-419)
- Modify: `tests/test_cli_commands.py` (delete `TestTaskList` class)

- [ ] **Step 1: Delete `task_list` function from `src/dida/cli.py`**

Remove the entire `task_list` function (lines 355-419, the `@task_app.command("list")` decorated function).

Also update the `task_app` help string from:
```python
task_app = typer.Typer(
    help="任务管理 (create/list/get/update/complete/delete)", no_args_is_help=True
)
```
to:
```python
task_app = typer.Typer(
    help="任务管理 (create/get/update/complete/delete/move/filter/completed)", no_args_is_help=True
)
```

- [ ] **Step 2: Delete `TestTaskList` class from `tests/test_cli_commands.py`**

Remove the entire `TestTaskList` class (including all its test methods: `test_list_all_tasks`, `test_list_filter_by_status_completed`, `test_list_filter_by_status_normal`, `test_list_filter_by_priority`, `test_list_filter_by_tag`, `test_list_with_limit`, `test_list_by_project`, `test_list_project_not_found`, `test_list_combined_filters`).

Also update `TestErrorHandling` — the two tests that use `task list` need to reference a different command. Change:
```python
result = runner.invoke(app, ["task", "list", "--json"])
```
to:
```python
result = runner.invoke(app, ["project", "list", "--json"])
```
in both `test_auth_error_json` and `test_api_error_json`.

- [ ] **Step 3: Run all tests to verify nothing is broken**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS (fewer tests than before, but all green)

- [ ] **Step 4: Commit**

```bash
git add src/dida/cli.py tests/test_cli_commands.py
git commit -m "refactor: remove task list command (replaced by task filter)"
```

---

### Task 3: Add `task move` CLI command

**Files:**
- Modify: `src/dida/cli.py` (add `task_move` function)
- Test: `tests/test_cli_commands.py` (add `TestTaskMove` class)

- [ ] **Step 1: Write failing tests for task move**

Add to `tests/test_cli_commands.py`:

```python
class TestTaskMove:
    """Tests for `dida task move` command."""

    def test_move_with_project_ids(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.move_task.return_value = [{"taskId": "t1", "etag": "abc"}]

            result = runner.invoke(
                app,
                ["task", "move", "t1", "--project-id", "p1", "--to-project-id", "p2", "--json"],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["success"] is True
            mock_client.move_task.assert_called_once_with("t1", "p1", "p2")

    def test_move_with_name_resolution(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [
                _make_project(id="p1", name="Work"),
                _make_project(id="p2", name="Personal"),
            ]
            mock_client.find_task_project_id.return_value = "p1"
            mock_client.move_task.return_value = [{"taskId": "t1", "etag": "abc"}]

            result = runner.invoke(
                app, ["task", "move", "t1", "--to", "Personal", "--json"]
            )
            assert result.exit_code == 0
            mock_client.move_task.assert_called_once_with("t1", "p1", "p2")

    def test_move_with_from_name(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [
                _make_project(id="p1", name="Work"),
                _make_project(id="p2", name="Personal"),
            ]
            mock_client.move_task.return_value = [{"taskId": "t1", "etag": "abc"}]

            result = runner.invoke(
                app, ["task", "move", "t1", "--from", "Work", "--to", "Personal", "--json"]
            )
            assert result.exit_code == 0
            mock_client.move_task.assert_called_once_with("t1", "p1", "p2")

    def test_move_missing_to(self):
        """Error when neither --to nor --to-project-id is provided."""
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(app, ["task", "move", "t1", "--json"])
            assert result.exit_code == 1

    def test_move_to_project_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = []

            result = runner.invoke(
                app, ["task", "move", "t1", "--to", "NonExistent", "--json"]
            )
            assert result.exit_code == 1

    def test_move_source_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [
                _make_project(id="p2", name="Personal"),
            ]
            mock_client.find_task_project_id.return_value = None

            result = runner.invoke(
                app, ["task", "move", "t1", "--to", "Personal", "--json"]
            )
            assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskMove -v`
Expected: FAIL (command not found)

- [ ] **Step 3: Implement `task_move` in `src/dida/cli.py`**

Add after `task_delete` function:

```python
@task_app.command("move")
def task_move(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    to: Annotated[str | None, typer.Option("--to", "-T", help="目标项目名称或 ID")] = None,
    from_project: Annotated[
        str | None, typer.Option("--from", "-F", help="源项目名称或 ID")
    ] = None,
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="源项目 ID (跳过自动查找)")
    ] = None,
    to_project_id: Annotated[
        str | None, typer.Option("--to-project-id", help="目标项目 ID (跳过模糊匹配)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """移动任务到另一个项目。"""
    client = _get_client()
    try:
        # Resolve destination
        dest_pid = to_project_id
        if not dest_pid:
            if not to:
                msg = "必须提供 --to 或 --to-project-id"
                if as_json:
                    output_error_json(msg, "VALIDATION_ERROR")
                else:
                    output_error(msg)
                raise typer.Exit(code=1)
            dest_pid = _resolve_project_id(client, to)
            if not dest_pid:
                msg = f"未找到目标项目: {to}"
                if as_json:
                    output_error_json(msg, "NOT_FOUND")
                else:
                    output_error(msg)
                raise typer.Exit(code=1)

        # Resolve source
        src_pid = project_id
        if not src_pid:
            if from_project:
                src_pid = _resolve_project_id(client, from_project)
            else:
                src_pid = client.find_task_project_id(task_id)
        if not src_pid:
            msg = f"未找到任务所在项目: {task_id}"
            if as_json:
                output_error_json(msg, "NOT_FOUND")
            else:
                output_error(msg)
            raise typer.Exit(code=1)

        result = client.move_task(task_id, src_pid, dest_pid)
        if as_json:
            output_json({"success": True, "data": result})
        else:
            output_success(f"已移动任务 {task_id} 到项目 {dest_pid}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskMove -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/dida/cli.py tests/test_cli_commands.py
git commit -m "feat: add task move command"
```

---

### Task 4: Add `task filter` CLI command

**Files:**
- Modify: `src/dida/cli.py` (add `task_filter` function)
- Test: `tests/test_cli_commands.py` (add `TestTaskFilter` class)

- [ ] **Step 1: Write failing tests for task filter**

Add to `tests/test_cli_commands.py`:

```python
class TestTaskFilter:
    """Tests for `dida task filter` command."""

    def test_filter_no_params(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.filter_tasks.return_value = [
                _make_task(id="t1", title="Task 1"),
            ]

            result = runner.invoke(app, ["task", "filter", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["success"] is True
            assert len(data["data"]) == 1

    def test_filter_by_project(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [_make_project(id="p1", name="Work")]
            mock_client.filter_tasks.return_value = [_make_task()]

            result = runner.invoke(app, ["task", "filter", "--project", "Work", "--json"])
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["project_ids"] == ["p1"]

    def test_filter_by_date_range(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.filter_tasks.return_value = []

            result = runner.invoke(
                app,
                ["task", "filter", "--start-date", "2026-03-01", "--end-date", "2026-03-31", "--json"],
            )
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["start_date"] is not None
            assert call_kwargs["end_date"] is not None

    def test_filter_by_priority(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.filter_tasks.return_value = [_make_task(priority=5)]

            result = runner.invoke(app, ["task", "filter", "--priority", "high,medium", "--json"])
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["priority"] == [5, 3]

    def test_filter_by_tag(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.filter_tasks.return_value = []

            result = runner.invoke(app, ["task", "filter", "--tag", "work,urgent", "--json"])
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["tags"] == ["work", "urgent"]

    def test_filter_by_status(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.filter_tasks.return_value = []

            result = runner.invoke(app, ["task", "filter", "--status", "normal", "--json"])
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["status"] == [0]

    def test_filter_combined(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [_make_project(id="p1", name="Work")]
            mock_client.filter_tasks.return_value = [_make_task(priority=5)]

            result = runner.invoke(
                app,
                ["task", "filter", "--project", "Work", "--priority", "high", "--status", "normal", "--json"],
            )
            assert result.exit_code == 0
            call_kwargs = mock_client.filter_tasks.call_args[1]
            assert call_kwargs["project_ids"] == ["p1"]
            assert call_kwargs["priority"] == [5]
            assert call_kwargs["status"] == [0]

    def test_filter_project_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = []

            result = runner.invoke(
                app, ["task", "filter", "--project", "NonExistent", "--json"]
            )
            assert result.exit_code == 1

    def test_filter_invalid_priority(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(app, ["task", "filter", "--priority", "urgent", "--json"])
            assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskFilter -v`
Expected: FAIL

- [ ] **Step 3: Implement `task_filter` in `src/dida/cli.py`**

Add after `task_move` function:

```python
def _parse_status_list(status_str: str) -> list[int]:
    """Parse comma-separated status names to API values."""
    mapping = {"normal": 0, "completed": 2}
    result = []
    for s in status_str.split(","):
        s = s.strip().lower()
        if s not in mapping:
            valid = ", ".join(mapping.keys())
            msg = f"Invalid status '{s}'. Valid values: {valid}"
            raise ValueError(msg)
        result.append(mapping[s])
    return result


def _parse_priority_list(priority_str: str) -> list[int]:
    """Parse comma-separated priority names to API values."""
    result = []
    for p in priority_str.split(","):
        result.append(TaskPriority.from_str(p.strip()).value)
    return result


@task_app.command("filter")
def task_filter(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    start_date: Annotated[
        str | None, typer.Option("--start-date", "-s", help="开始日期过滤")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option("--end-date", "-e", help="结束日期过滤")
    ] = None,
    priority: Annotated[
        str | None,
        typer.Option("--priority", "-p", help="优先级过滤 (逗号分隔: none/low/medium/high)"),
    ] = None,
    tag: Annotated[
        str | None, typer.Option("--tag", help="标签过滤 (逗号分隔, AND 逻辑)")
    ] = None,
    status: Annotated[
        str | None, typer.Option("--status", help="状态过滤 (逗号分隔: normal/completed)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """过滤查询任务。支持按项目、日期、优先级、标签、状态过滤。"""
    client = _get_client()
    try:
        project_ids = None
        if project:
            pid = _resolve_project_id(client, project)
            if pid is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_ids = [pid]

        parsed_start = _parse_date(start_date) if start_date else None
        parsed_end = _parse_date(end_date) if end_date else None
        parsed_priority = _parse_priority_list(priority) if priority else None
        parsed_tags = [t.strip() for t in tag.split(",")] if tag else None
        parsed_status = _parse_status_list(status) if status else None

        tasks = client.filter_tasks(
            project_ids=project_ids,
            start_date=parsed_start,
            end_date=parsed_end,
            priority=parsed_priority,
            tags=parsed_tags,
            status=parsed_status,
        )
        display_tasks(tasks, as_json=as_json)
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskFilter -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/dida/cli.py tests/test_cli_commands.py
git commit -m "feat: add task filter command"
```

---

### Task 5: Add `task completed` CLI command

**Files:**
- Modify: `src/dida/cli.py` (add `task_completed` function)
- Test: `tests/test_cli_commands.py` (add `TestTaskCompleted` class)

- [ ] **Step 1: Write failing tests for task completed**

Add to `tests/test_cli_commands.py`:

```python
class TestTaskCompleted:
    """Tests for `dida task completed` command."""

    def test_completed_no_params(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_completed_tasks.return_value = [
                _make_task(id="t1", title="Done", status=2),
            ]

            result = runner.invoke(app, ["task", "completed", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["success"] is True
            assert len(data["data"]) == 1

    def test_completed_by_project(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [_make_project(id="p1", name="Work")]
            mock_client.list_completed_tasks.return_value = [_make_task(status=2)]

            result = runner.invoke(
                app, ["task", "completed", "--project", "Work", "--json"]
            )
            assert result.exit_code == 0
            call_kwargs = mock_client.list_completed_tasks.call_args[1]
            assert call_kwargs["project_ids"] == ["p1"]

    def test_completed_by_date_range(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_completed_tasks.return_value = []

            result = runner.invoke(
                app,
                ["task", "completed", "--start-date", "2026-03-01", "--end-date", "2026-03-31", "--json"],
            )
            assert result.exit_code == 0
            call_kwargs = mock_client.list_completed_tasks.call_args[1]
            assert call_kwargs["start_date"] is not None
            assert call_kwargs["end_date"] is not None

    def test_completed_project_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = []

            result = runner.invoke(
                app, ["task", "completed", "--project", "NonExistent", "--json"]
            )
            assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskCompleted -v`
Expected: FAIL

- [ ] **Step 3: Implement `task_completed` in `src/dida/cli.py`**

Add after `task_filter` function:

```python
@task_app.command("completed")
def task_completed(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    start_date: Annotated[
        str | None, typer.Option("--start-date", "-s", help="完成时间起始")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option("--end-date", "-e", help="完成时间结束")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """查看已完成任务。按完成时间范围过滤。"""
    client = _get_client()
    try:
        project_ids = None
        if project:
            pid = _resolve_project_id(client, project)
            if pid is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_ids = [pid]

        parsed_start = _parse_date(start_date) if start_date else None
        parsed_end = _parse_date(end_date) if end_date else None

        tasks = client.list_completed_tasks(
            project_ids=project_ids,
            start_date=parsed_start,
            end_date=parsed_end,
        )
        display_tasks(tasks, as_json=as_json)
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_commands.py::TestTaskCompleted -v`
Expected: ALL PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/dida/cli.py tests/test_cli_commands.py
git commit -m "feat: add task completed command"
```

---

### Task 6: Bump version to 0.3.0

**Files:**
- Modify: `pyproject.toml` (line 3)
- Modify: `src/dida/__init__.py` (line 3)

- [ ] **Step 1: Update version in `pyproject.toml`**

Change `version = "0.2.0"` to `version = "0.3.0"`.

- [ ] **Step 2: Update version in `src/dida/__init__.py`**

Change `__version__ = "0.2.0"` to `__version__ = "0.3.0"`.

- [ ] **Step 3: Update version test in `tests/test_cli_commands.py`**

In `TestVersionFlag.test_version_output`, change:
```python
assert "dida 0.2.0" in result.output
```
to:
```python
assert "dida 0.3.0" in result.output
```

- [ ] **Step 4: Run tests to verify**

Run: `uv run pytest tests/test_cli_commands.py::TestVersionFlag -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/dida/__init__.py tests/test_cli_commands.py
git commit -m "chore: bump version to 0.3.0"
```

---

### Task 7: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `skill/dida365/SKILL.md`
- Modify: `skill/dida365/references/api-ref.md`

- [ ] **Step 1: Update `README.md`**

Changes needed:
1. In the Tasks section, replace `task list` examples with `task filter` and `task completed` examples
2. Add `task move` examples
3. Update the parameter table — remove `task list` mention, no longer applicable
4. In "Known Limitations", remove item 2 about "No Inbox API" since filter replaces list
5. In "Deprecated Commands" table, add `task list` → `task filter`
6. Update version reference from `0.2.0` to `0.3.0`

Replace the Tasks bash example block with:

```bash
# 创建任务 (支持所有 API 参数)
dida task create "Buy milk" --priority high --due tomorrow --project "Shopping"
dida task create "Weekly meeting" --repeat "RRULE:FREQ=WEEKLY;INTERVAL=1" --all-day
dida task create "Big task" --items '[{"title":"Step 1"},{"title":"Step 2"}]'
dida task create "Tagged" --tags "work,urgent" --start-date 2026-03-20

# 过滤查询任务
dida task filter                                  # 所有任务
dida task filter --project "Work"                 # 按项目
dida task filter --priority high                  # 按优先级
dida task filter --status normal                  # 未完成任务
dida task filter --tag "urgent"                   # 按标签
dida task filter --start-date 2026-03-01 --end-date 2026-03-31

# 查看已完成任务
dida task completed                               # 所有已完成
dida task completed --project "Work"              # 按项目
dida task completed --start-date 2026-03-01       # 按完成时间

# 移动任务到另一个项目
dida task move <task_id> --to "Personal"
dida task move <task_id> --from "Work" --to "Personal"

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

Add new parameter tables after the existing create/update table:

```markdown
#### task filter 参数

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | 项目名称或 ID |
| `--start-date` | `-s` | 开始日期过滤 |
| `--end-date` | `-e` | 结束日期过滤 |
| `--priority` | `-p` | 优先级 (逗号分隔: none/low/medium/high) |
| `--tag` | | 标签 (逗号分隔, AND 逻辑) |
| `--status` | | 状态 (逗号分隔: normal/completed) |

#### task completed 参数

| Option | Short | Description |
|---|---|---|
| `--project` | `-P` | 项目名称或 ID |
| `--start-date` | `-s` | 完成时间起始 |
| `--end-date` | `-e` | 完成时间结束 |

#### task move 参数

| Option | Short | Description |
|---|---|---|
| `--to` | `-T` | 目标项目名称或 ID (必填) |
| `--from` | `-F` | 源项目名称或 ID |
| `--project-id` | | 源项目 ID (跳过自动查找) |
| `--to-project-id` | | 目标项目 ID (跳过模糊匹配) |
```

Update Deprecated Commands table — add row: `task list` → `task filter`.

Update version: `dida 0.3.0`.

Remove Known Limitations item 2 ("No Inbox API").

- [ ] **Step 2: Update `skill/dida365/SKILL.md`**

1. Bump version in frontmatter from `0.2.0` to `0.3.0`
2. Remove the `task list` section under Command Reference
3. Add sections for `task move`, `task filter`, `task completed` with option tables
4. Update Workflow Patterns to use `task filter` instead of `task list`

- [ ] **Step 3: Update `skill/dida365/references/api-ref.md`**

1. Remove the `dida task list` section
2. Add new sections for `dida task move`, `dida task filter`, `dida task completed` with full option tables matching existing format

- [ ] **Step 4: Run lint check**

Run: `uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add README.md skill/dida365/SKILL.md skill/dida365/references/api-ref.md
git commit -m "docs: update README, SKILL, and api-ref for v0.3.0

Remove task list references, add task move/filter/completed docs.
Bump skill version to 0.3.0."
```
