"""Tests for --project-id option on task commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dida.cli import app

runner = CliRunner()


class TestTaskDoneProjectId:
    """Test that --project-id skips find_task_project_id lookup."""

    def test_done_with_project_id_skips_lookup(self):
        """When --project-id is provided, should NOT call find_task_project_id."""
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            runner.invoke(
                app,
                ["task", "done", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.complete_task.assert_called_once_with("proj456", "task123")

    def test_done_without_project_id_calls_lookup(self):
        """When --project-id is NOT provided, should call find_task_project_id."""
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.find_task_project_id.return_value = "found_proj"

            runner.invoke(
                app,
                ["task", "done", "task123", "--json"],
            )

            mock_client.find_task_project_id.assert_called_once_with("task123")
            mock_client.complete_task.assert_called_once_with("found_proj", "task123")


class TestTaskDeleteProjectId:
    """Test that --project-id skips find_task_project_id lookup on delete."""

    def test_delete_with_project_id_skips_lookup(self):
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            runner.invoke(
                app,
                ["task", "delete", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.delete_task.assert_called_once_with("proj456", "task123")


class TestTaskUpdateProjectId:
    """Test that --project-id skips find_task_project_id lookup on update."""

    def test_update_with_project_id_skips_lookup(self):
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.update_task.return_value = MagicMock(
                to_json_dict=lambda: {"id": "task123", "title": "new title"}
            )

            runner.invoke(
                app,
                [
                    "task",
                    "update",
                    "task123",
                    "--project-id",
                    "proj456",
                    "--title",
                    "new title",
                    "--json",
                ],
            )

            mock_client.find_task_project_id.assert_not_called()


class TestTaskListActiveOnly:
    """Test that task list defaults to active projects only."""

    def test_list_skips_closed_projects(self):
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            from dida.models import Project, ProjectData

            active_project = Project(id="active1", name="Active", closed=False)
            closed_project = Project(id="closed1", name="Closed", closed=True)
            mock_client.list_projects.return_value = [active_project, closed_project]
            mock_client.get_project_data.return_value = ProjectData(
                project=active_project, tasks=[]
            )

            runner.invoke(app, ["task", "list", "--json"])

            # Should only query the active project, not the closed one
            mock_client.get_project_data.assert_called_once_with("active1")

    def test_list_all_includes_closed_projects(self):
        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            from dida.models import Project, ProjectData

            active_project = Project(id="active1", name="Active", closed=False)
            closed_project = Project(id="closed1", name="Closed", closed=True)
            mock_client.list_projects.return_value = [active_project, closed_project]
            mock_client.get_project_data.return_value = ProjectData(
                project=active_project, tasks=[]
            )

            runner.invoke(app, ["task", "list", "--all", "--json"])

            # Should query both projects
            assert mock_client.get_project_data.call_count == 2


class TestErrorOutput:
    """Test that error JSON is output exactly once."""

    def test_auth_error_json_output_once(self):
        """AuthError JSON should appear exactly once in stdout."""
        import json

        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            from dida.client import AuthError

            mock_client.complete_task.side_effect = AuthError()

            result = runner.invoke(
                app,
                ["task", "done", "task123", "--project-id", "proj456", "--json"],
            )

            # stdout should contain exactly one JSON error object
            output = result.output.strip()
            parsed = json.loads(output)
            assert parsed["code"] == "AUTH_ERROR"

    def test_api_error_json_output_once(self):
        """ApiError JSON should appear exactly once in stdout."""
        import json

        with patch("dida.cli.DidaClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            from dida.client import ApiError

            mock_client.complete_task.side_effect = ApiError("test error", status_code=500)

            result = runner.invoke(
                app,
                ["task", "done", "task123", "--project-id", "proj456", "--json"],
            )

            output = result.output.strip()
            parsed = json.loads(output)
            assert parsed["error"] == "test error"
            assert parsed["code"] == "API_ERROR"
