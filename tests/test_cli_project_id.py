"""Tests for --project-id option on task commands.

Tests both new command names (complete/delete) and deprecated aliases (done).
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dida.cli import app

runner = CliRunner()


class TestTaskCompleteProjectId:
    """Test that --project-id skips find_task_project_id lookup on complete."""

    def test_complete_with_project_id_skips_lookup(self):
        """When --project-id is provided, should NOT call find_task_project_id."""
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            runner.invoke(
                app,
                ["task", "complete", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.complete_task.assert_called_once_with("proj456", "task123")

    def test_complete_without_project_id_calls_lookup(self):
        """When --project-id is NOT provided, should call find_task_project_id."""
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            mock_client.find_task_project_id.return_value = "found_proj"

            runner.invoke(
                app,
                ["task", "complete", "task123", "--json"],
            )

            mock_client.find_task_project_id.assert_called_once_with("task123")
            mock_client.complete_task.assert_called_once_with("found_proj", "task123")


class TestTaskDoneProjectId:
    """Test deprecated 'done' alias still works with --project-id."""

    def test_done_with_project_id_skips_lookup(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            runner.invoke(
                app,
                ["task", "done", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.complete_task.assert_called_once_with("proj456", "task123")

    def test_done_without_project_id_calls_lookup(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
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
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client

            runner.invoke(
                app,
                ["task", "delete", "task123", "--project-id", "proj456", "--json"],
            )

            mock_client.find_task_project_id.assert_not_called()
            mock_client.delete_task.assert_called_once_with("proj456", "task123")


class TestTaskUpdateProjectId:
    """Test that --project-id skips find_task_project_id lookup on update."""

    def test_update_with_project_id_skips_lookup(self):
        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
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


class TestErrorOutput:
    """Test that error JSON is output exactly once."""

    def test_auth_error_json_output_once(self):
        """AuthError JSON should appear exactly once in stdout."""
        import json

        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            from dida.client import AuthError

            mock_client.complete_task.side_effect = AuthError()

            result = runner.invoke(
                app,
                ["task", "complete", "task123", "--project-id", "proj456", "--json"],
            )

            # stdout should contain exactly one JSON error object
            output = result.output.strip()
            parsed = json.loads(output)
            assert parsed["code"] == "AUTH_ERROR"

    def test_api_error_json_output_once(self):
        """ApiError JSON should appear exactly once in stdout."""
        import json

        with patch("dida.cli._get_client") as mock_gc:
            mock_client = MagicMock()
            mock_gc.return_value = mock_client
            from dida.client import ApiError

            mock_client.complete_task.side_effect = ApiError("test error", status_code=500)

            result = runner.invoke(
                app,
                ["task", "complete", "task123", "--project-id", "proj456", "--json"],
            )

            output = result.output.strip()
            parsed = json.loads(output)
            assert parsed["error"] == "test error"
            assert parsed["code"] == "API_ERROR"
