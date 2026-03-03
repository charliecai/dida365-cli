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
