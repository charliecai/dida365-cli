"""Tests for dida.client module."""

from unittest.mock import patch

import httpx
import pytest
import respx

from dida.client import ApiError, AuthError, DidaClient
from dida.models import Task


@pytest.fixture
def mock_token():
    """Mock a valid access token."""
    with (
        patch("dida.client.get_access_token", return_value="test_token"),
        patch("dida.client.refresh_access_token", return_value=None),
    ):
        yield


@pytest.fixture
def client(mock_token):
    """Create a DidaClient with mocked auth."""
    c = DidaClient()
    yield c
    c.close()


class TestDidaClient:
    """Tests for DidaClient API methods."""

    @respx.mock
    def test_list_projects(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "p1", "name": "Work"},
                    {"id": "p2", "name": "Personal"},
                ],
            )
        )
        projects = client.list_projects()
        assert len(projects) == 2
        assert projects[0].name == "Work"

    @respx.mock
    def test_get_project_data(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project/p1/data").mock(
            return_value=httpx.Response(
                200,
                json={
                    "project": {"id": "p1", "name": "Work"},
                    "tasks": [{"id": "t1", "title": "Task 1"}],
                },
            )
        )
        pd = client.get_project_data("p1")
        assert pd.project.name == "Work"
        assert len(pd.tasks) == 1

    @respx.mock
    def test_create_task(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task").mock(
            return_value=httpx.Response(
                200,
                json={"id": "new1", "title": "New task", "projectId": "", "priority": 0},
            )
        )
        task = Task(title="New task")
        created = client.create_task(task)
        assert created.id == "new1"
        assert created.title == "New task"

    @respx.mock
    def test_complete_task(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/project/p1/task/t1/complete").mock(
            return_value=httpx.Response(200, json={})
        )
        # Should not raise
        client.complete_task("p1", "t1")

    @respx.mock
    def test_delete_task(self, client: DidaClient) -> None:
        respx.delete("https://api.dida365.com/open/v1/task/p1/t1").mock(
            return_value=httpx.Response(204)
        )
        # Should not raise
        client.delete_task("p1", "t1")

    @respx.mock
    def test_api_error_on_400(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(400, text="Bad Request")
        )
        with pytest.raises(ApiError, match="API 错误"):
            client.list_projects()

    @respx.mock
    def test_auth_error_on_401(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(AuthError):
            client.list_projects()

    def test_auth_error_when_no_token(self) -> None:
        with patch("dida.client.get_access_token", return_value=None):
            c = DidaClient()
            with pytest.raises(AuthError):
                c.list_projects()
            c.close()

    @respx.mock
    def test_find_project_by_name(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "p1", "name": "Work"},
                    {"id": "p2", "name": "Personal"},
                    {"id": "p3", "name": "Workout"},
                ],
            )
        )
        matches = client.find_project_by_name("work")
        assert len(matches) == 2  # "Work" and "Workout"
        assert matches[0].name == "Work"
