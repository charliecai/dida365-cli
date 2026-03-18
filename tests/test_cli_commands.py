"""Comprehensive tests for all CLI commands (v0.2.0)."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dida.cli import app
from dida.models import Project, ProjectData, Task

runner = CliRunner()


# ── Helpers ──────────────────────────────────────────────────────────


def _mock_client(**overrides):
    """Create a MagicMock DidaClient with sensible defaults."""
    mock = MagicMock()
    mock.list_projects.return_value = []
    mock.get_project_data.return_value = ProjectData(
        project=Project(id="p1", name="Work"), tasks=[]
    )
    for k, v in overrides.items():
        setattr(mock, k, v) if not callable(v) else None
    return mock


def _make_task(**kwargs) -> Task:
    defaults = {"id": "t1", "project_id": "p1", "title": "Test task", "priority": 0, "status": 0}
    defaults.update(kwargs)
    return Task(**defaults)


def _make_project(**kwargs) -> Project:
    defaults = {"id": "p1", "name": "Work", "color": "#ff0000"}
    defaults.update(kwargs)
    return Project(**defaults)


# ── Version flag ─────────────────────────────────────────────────────


class TestVersionFlag:
    def test_version_output(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "dida 0.2.0" in result.output

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "dida" in result.output


# ── Task create ──────────────────────────────────────────────────────
class TestTaskCreate:
    """Tests for `dida task create` command."""

    def test_create_minimal(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.return_value = _make_task(title="Buy milk")

            result = runner.invoke(app, ["task", "create", "Buy milk", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["success"] is True
            assert data["data"]["title"] == "Buy milk"

    def test_create_with_priority(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.return_value = _make_task(title="Urgent", priority=5)

            result = runner.invoke(
                app, ["task", "create", "Urgent", "--priority", "high", "--json"]
            )
            assert result.exit_code == 0
            # Verify the task passed to create_task had priority set
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.priority == 5

    def test_create_with_due_date(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.return_value = _make_task(title="Due task")

            result = runner.invoke(
                app, ["task", "create", "Due task", "--due", "tomorrow", "--json"]
            )
            assert result.exit_code == 0
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.due_date is not None

    def test_create_with_project(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [_make_project()]
            mock_client.create_task.return_value = _make_task(project_id="p1")

            result = runner.invoke(
                app, ["task", "create", "Task", "--project", "Work", "--json"]
            )
            assert result.exit_code == 0
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.project_id == "p1"

    def test_create_with_all_options(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.return_value = _make_task(title="Full task")

            result = runner.invoke(
                app,
                [
                    "task", "create", "Full task",
                    "--content", "notes here",
                    "--desc", "description",
                    "--tags", "work,urgent",
                    "--all-day",
                    "--start-date", "2026-03-20",
                    "--due", "2026-03-25",
                    "--timezone", "America/New_York",
                    "--reminders", "TRIGGER:PT0S",
                    "--repeat", "RRULE:FREQ=DAILY;INTERVAL=1",
                    "--priority", "medium",
                    "--sort-order", "100",
                    "--items", '[{"title":"Step 1"}]',
                    "--json",
                ],
            )
            assert result.exit_code == 0
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.content == "notes here"
            assert call_args.desc == "description"
            assert call_args.tags == ["work", "urgent"]
            assert call_args.all_day is True
            assert call_args.time_zone == "America/New_York"
            assert call_args.reminders == ["TRIGGER:PT0S"]
            assert call_args.repeat_flag == "RRULE:FREQ=DAILY;INTERVAL=1"
            assert call_args.priority == 3  # medium
            assert call_args.sort_order == 100
            assert len(call_args.items) == 1

    def test_create_invalid_priority(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(
                app, ["task", "create", "Bad", "--priority", "urgent", "--json"]
            )
            assert result.exit_code == 1

    def test_create_invalid_date(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(
                app, ["task", "create", "Bad", "--due", "not-a-date", "--json"]
            )
            assert result.exit_code == 1


class TestTaskGet:
    """Tests for `dida task get` command."""

    def test_get_with_project_id(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.get_task.return_value = _make_task(title="Found task")

            result = runner.invoke(
                app, ["task", "get", "t1", "--project-id", "p1", "--json"]
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["title"] == "Found task"
            mock_client.find_task_project_id.assert_not_called()

    def test_get_without_project_id_auto_lookup(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "p1"
            mock_client.get_task.return_value = _make_task(title="Found task")

            result = runner.invoke(app, ["task", "get", "t1", "--json"])
            assert result.exit_code == 0
            mock_client.find_task_project_id.assert_called_once_with("t1")

    def test_get_task_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = None

            result = runner.invoke(app, ["task", "get", "nonexistent", "--json"])
            assert result.exit_code == 1


class TestTaskUpdate:
    """Tests for `dida task update` command."""

    def test_update_title(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "p1"
            mock_client.update_task.return_value = _make_task(title="New title")

            result = runner.invoke(
                app, ["task", "update", "t1", "--title", "New title", "--json"]
            )
            assert result.exit_code == 0
            call_args = mock_client.update_task.call_args[0][0]
            assert call_args.title == "New title"

    def test_update_with_project_id(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.update_task.return_value = _make_task()

            result = runner.invoke(
                app,
                ["task", "update", "t1", "--project-id", "p1", "--title", "X", "--json"],
            )
            assert result.exit_code == 0
            mock_client.find_task_project_id.assert_not_called()

    def test_update_all_options(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "p1"
            mock_client.update_task.return_value = _make_task()

            result = runner.invoke(
                app,
                [
                    "task", "update", "t1",
                    "--title", "Updated",
                    "--content", "new content",
                    "--desc", "new desc",
                    "--tags", "a,b",
                    "--all-day",
                    "--start-date", "2026-04-01",
                    "--due", "2026-04-10",
                    "--timezone", "UTC",
                    "--reminders", "TRIGGER:PT0S",
                    "--repeat", "RRULE:FREQ=WEEKLY;INTERVAL=1",
                    "--priority", "low",
                    "--sort-order", "50",
                    "--items", '[{"title":"Sub"}]',
                    "--json",
                ],
            )
            assert result.exit_code == 0
            call_args = mock_client.update_task.call_args[0][0]
            assert call_args.title == "Updated"
            assert call_args.content == "new content"
            assert call_args.tags == ["a", "b"]
            assert call_args.priority == 1  # low

    def test_update_task_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = None

            result = runner.invoke(
                app, ["task", "update", "bad", "--title", "X", "--json"]
            )
            assert result.exit_code == 1


class TestTaskComplete:
    """Tests for `dida task complete` command."""

    def test_complete_with_project_id(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(
                app, ["task", "complete", "t1", "--project-id", "p1", "--json"]
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["status"] == "completed"
            mock_client.complete_task.assert_called_once_with("p1", "t1")

    def test_complete_auto_lookup(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "p1"

            result = runner.invoke(app, ["task", "complete", "t1", "--json"])
            assert result.exit_code == 0
            mock_client.find_task_project_id.assert_called_once_with("t1")

    def test_complete_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = None

            result = runner.invoke(app, ["task", "complete", "bad", "--json"])
            assert result.exit_code == 1


class TestTaskDelete:
    """Tests for `dida task delete` command."""

    def test_delete_with_project_id_json(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(
                app, ["task", "delete", "t1", "--project-id", "p1", "--json"]
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["status"] == "deleted"
            mock_client.delete_task.assert_called_once_with("p1", "t1")

    def test_delete_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = None

            result = runner.invoke(app, ["task", "delete", "bad", "--json"])
            assert result.exit_code == 1


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


class TestTaskBatchCreate:
    """Tests for `dida task batch-create` command."""

    def test_batch_create(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.batch_create_tasks.return_value = [
                _make_task(id="t1", title="Task 1"),
                _make_task(id="t2", title="Task 2"),
            ]

            input_data = json.dumps([{"title": "Task 1"}, {"title": "Task 2"}])
            result = runner.invoke(app, ["task", "batch-create", "--json"], input=input_data)
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["count"] == 2

    def test_batch_create_invalid_json(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(app, ["task", "batch-create", "--json"], input="not json")
            assert result.exit_code == 1

    def test_batch_create_not_array(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(
                app, ["task", "batch-create", "--json"], input='{"title":"single"}'
            )
            assert result.exit_code == 1


class TestProjectCreate:
    """Tests for `dida project create` command."""

    def test_create_minimal(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_project.return_value = _make_project(name="Shopping")

            result = runner.invoke(app, ["project", "create", "Shopping", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["name"] == "Shopping"

    def test_create_with_all_options(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_project.return_value = _make_project(
                name="Kanban", color="#4A90D9", view_mode="kanban", kind="TASK"
            )

            result = runner.invoke(
                app,
                [
                    "project", "create", "Kanban",
                    "--color", "#4A90D9",
                    "--view-mode", "kanban",
                    "--kind", "TASK",
                    "--sort-order", "10",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            call_args = mock_client.create_project.call_args[0][0]
            assert call_args.name == "Kanban"
            assert call_args.color == "#4A90D9"
            assert call_args.view_mode == "kanban"
            assert call_args.kind == "TASK"
            assert call_args.sort_order == 10


class TestProjectList:
    """Tests for `dida project list` command."""

    def test_list_projects(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [
                _make_project(id="p1", name="Work"),
                _make_project(id="p2", name="Personal"),
            ]

            result = runner.invoke(app, ["project", "list", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data["data"]) == 2

    def test_list_empty(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = []

            result = runner.invoke(app, ["project", "list", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"] == []


class TestProjectGet:
    """Tests for `dida project get` command."""

    def test_get_by_id(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.get_project_data.return_value = ProjectData(
                project=_make_project(id="p1", name="Work"),
                tasks=[_make_task()],
            )

            result = runner.invoke(app, ["project", "get", "p1", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["project"]["name"] == "Work"

    def test_get_by_name_fuzzy(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            # First call (try as ID) raises ApiError
            from dida.client import ApiError
            mock_client.get_project_data.side_effect = [
                ApiError("not found", status_code=404),
                ProjectData(project=_make_project(name="Work"), tasks=[]),
            ]
            mock_client.find_project_by_name.return_value = [_make_project(name="Work")]

            result = runner.invoke(app, ["project", "get", "work", "--json"])
            assert result.exit_code == 0

    def test_get_not_found(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            from dida.client import ApiError
            mock_client.get_project_data.side_effect = ApiError("not found", status_code=404)
            mock_client.find_project_by_name.return_value = []
            mock_client.list_projects.return_value = []

            result = runner.invoke(app, ["project", "get", "nonexistent", "--json"])
            assert result.exit_code == 1


class TestProjectUpdate:
    """Tests for `dida project update` command."""

    def test_update_name(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.update_project.return_value = _make_project(name="New Name")

            result = runner.invoke(
                app, ["project", "update", "p1", "--name", "New Name", "--json"]
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["name"] == "New Name"

    def test_update_all_options(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.update_project.return_value = _make_project()

            result = runner.invoke(
                app,
                [
                    "project", "update", "p1",
                    "--name", "Updated",
                    "--color", "#000",
                    "--view-mode", "kanban",
                    "--kind", "NOTE",
                    "--sort-order", "5",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            call_args = mock_client.update_project.call_args
            assert call_args[0][0] == "p1"  # project_id
            proj = call_args[0][1]
            assert proj.name == "Updated"
            assert proj.color == "#000"
            assert proj.view_mode == "kanban"
            assert proj.kind == "NOTE"
            assert proj.sort_order == 5


class TestProjectDelete:
    """Tests for `dida project delete` command."""

    def test_delete_json(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            result = runner.invoke(app, ["project", "delete", "p1", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["data"]["status"] == "deleted"
            mock_client.delete_project.assert_called_once_with("p1")


class TestDeprecatedAliases:
    """Tests for deprecated command aliases."""

    def test_task_add_delegates_to_create(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.return_value = _make_task(title="Via add")

            result = runner.invoke(app, ["task", "add", "Via add", "--json"])
            assert result.exit_code == 0
            mock_client.create_task.assert_called_once()

    def test_task_done_delegates_to_complete(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "p1"

            result = runner.invoke(app, ["task", "done", "t1", "--json"])
            assert result.exit_code == 0
            mock_client.complete_task.assert_called_once()

    def test_task_batch_add_delegates_to_batch_create(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.batch_create_tasks.return_value = [_make_task()]

            input_data = json.dumps([{"title": "T1"}])
            result = runner.invoke(app, ["task", "batch-add", "--json"], input=input_data)
            assert result.exit_code == 0
            mock_client.batch_create_tasks.assert_called_once()

    def test_project_show_delegates_to_get(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.get_project_data.return_value = ProjectData(
                project=_make_project(), tasks=[]
            )

            result = runner.invoke(app, ["project", "show", "p1", "--json"])
            assert result.exit_code == 0
            mock_client.get_project_data.assert_called()


class TestSetupCommand:
    """Tests for `dida setup` command."""

    def test_setup_json_all_ok(self):
        with patch("dida.cli.load_token", return_value={"access_token": "tok"}):
            result = runner.invoke(app, ["setup", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True
            assert all(c["ok"] for c in data["checks"])

    def test_setup_json_no_auth(self):
        with patch("dida.cli.load_token", return_value=None):
            result = runner.invoke(app, ["setup", "--json"])
            assert result.exit_code == 1
            data = json.loads(result.output)
            assert data["ok"] is False


class TestAuthCommands:
    """Tests for auth status/logout commands."""

    def test_auth_status_authenticated(self):
        with patch("dida.cli.load_token", return_value={"access_token": "tok"}):
            result = runner.invoke(app, ["auth", "status", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["authenticated"] is True

    def test_auth_status_not_authenticated(self):
        with patch("dida.cli.load_token", return_value=None):
            result = runner.invoke(app, ["auth", "status", "--json"])
            assert result.exit_code == 2
            data = json.loads(result.output)
            assert data["authenticated"] is False

    def test_auth_logout_success(self):
        with patch("dida.cli.delete_token", return_value=True):
            result = runner.invoke(app, ["auth", "logout"])
            assert result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling across commands."""

    def test_auth_error_json(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            from dida.client import AuthError
            mock_client.list_projects.side_effect = AuthError()

            result = runner.invoke(app, ["project", "list", "--json"])
            assert result.exit_code == 2
            data = json.loads(result.output)
            assert data["code"] == "AUTH_ERROR"

    def test_api_error_json(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            from dida.client import ApiError
            mock_client.list_projects.side_effect = ApiError("server error", status_code=500)

            result = runner.invoke(app, ["project", "list", "--json"])
            assert result.exit_code == 1
            data = json.loads(result.output)
            assert data["code"] == "API_ERROR"

    def test_unknown_error_json(self):
        """RuntimeError in task create goes through _handle_error."""
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.create_task.side_effect = RuntimeError("boom")

            result = runner.invoke(app, ["task", "create", "Test", "--json"])
            # RuntimeError is not caught by task_create's except clauses,
            # so it propagates as an unhandled exception
            assert result.exit_code == 1


class TestResolveProjectId:
    """Tests for _resolve_project_id helper via CLI."""

    def test_resolve_by_exact_id(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [_make_project(id="p1", name="Work")]
            mock_client.create_task.return_value = _make_task()

            result = runner.invoke(
                app, ["task", "create", "T", "--project", "p1", "--json"]
            )
            assert result.exit_code == 0
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.project_id == "p1"

    def test_resolve_by_fuzzy_name(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.list_projects.return_value = [
                _make_project(id="p1", name="Shopping List"),
            ]
            mock_client.create_task.return_value = _make_task()

            result = runner.invoke(
                app, ["task", "create", "T", "--project", "shopping", "--json"]
            )
            assert result.exit_code == 0
            call_args = mock_client.create_task.call_args[0][0]
            assert call_args.project_id == "p1"
