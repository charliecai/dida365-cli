"""Tests for dida.client module."""

from unittest.mock import patch

import httpx
import pytest
import respx

from dida.client import ApiError, AuthError, DidaClient
from dida.models import Project, Task


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

    # --- Project endpoints ---

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
    def test_get_project(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project/p1").mock(
            return_value=httpx.Response(
                200,
                json={"id": "p1", "name": "Work", "color": "#ff0000"},
            )
        )
        project = client.get_project("p1")
        assert project.id == "p1"
        assert project.name == "Work"
        assert project.color == "#ff0000"

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
    def test_create_project(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(
                200,
                json={"id": "new_p", "name": "Shopping", "color": "#abc"},
            )
        )
        proj = Project(name="Shopping", color="#abc")
        created = client.create_project(proj)
        assert created.id == "new_p"
        assert created.name == "Shopping"

    @respx.mock
    def test_update_project(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/project/p1").mock(
            return_value=httpx.Response(
                200,
                json={"id": "p1", "name": "Updated", "color": "#000"},
            )
        )
        proj = Project(name="Updated", color="#000")
        updated = client.update_project("p1", proj)
        assert updated.name == "Updated"

    @respx.mock
    def test_delete_project(self, client: DidaClient) -> None:
        respx.delete("https://api.dida365.com/open/v1/project/p1").mock(
            return_value=httpx.Response(204)
        )
        # Should not raise
        client.delete_project("p1")

    # --- Task endpoints ---

    @respx.mock
    def test_get_task(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project/p1/task/t1").mock(
            return_value=httpx.Response(
                200,
                json={"id": "t1", "title": "My task", "projectId": "p1", "priority": 3},
            )
        )
        task = client.get_task("p1", "t1")
        assert task.id == "t1"
        assert task.title == "My task"
        assert task.priority == 3

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
    def test_update_task(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/task/t1").mock(
            return_value=httpx.Response(
                200,
                json={"id": "t1", "title": "Updated", "projectId": "p1", "priority": 5},
            )
        )
        task = Task(id="t1", project_id="p1", title="Updated", priority=5)
        updated = client.update_task(task)
        assert updated.title == "Updated"
        assert updated.priority == 5

    @respx.mock
    def test_complete_task(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/project/p1/task/t1/complete").mock(
            return_value=httpx.Response(200, json={})
        )
        # Should not raise
        client.complete_task("p1", "t1")

    @respx.mock
    def test_delete_task(self, client: DidaClient) -> None:
        respx.delete("https://api.dida365.com/open/v1/project/p1/task/t1").mock(
            return_value=httpx.Response(204)
        )
        # Should not raise
        client.delete_task("p1", "t1")

    @respx.mock
    def test_batch_create_tasks(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/batch/task").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "t1", "title": "Task 1"},
                    {"id": "t2", "title": "Task 2"},
                ],
            )
        )
        tasks = [Task(title="Task 1"), Task(title="Task 2")]
        created = client.batch_create_tasks(tasks)
        assert len(created) == 2
        assert created[0].title == "Task 1"

    @respx.mock
    def test_batch_create_tasks_empty_response(self, client: DidaClient) -> None:
        respx.post("https://api.dida365.com/open/v1/batch/task").mock(
            return_value=httpx.Response(200, json={})
        )
        tasks = [Task(title="Task 1")]
        created = client.batch_create_tasks(tasks)
        assert created == []

    # --- Error handling ---

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

    # --- Helper methods ---

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

    @respx.mock
    def test_find_task_project_id_found(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(
                200, json=[{"id": "p1", "name": "Work"}]
            )
        )
        respx.get("https://api.dida365.com/open/v1/project/p1/data").mock(
            return_value=httpx.Response(
                200,
                json={
                    "project": {"id": "p1", "name": "Work"},
                    "tasks": [{"id": "target_task", "title": "Found"}],
                },
            )
        )
        result = client.find_task_project_id("target_task")
        assert result == "p1"

    @respx.mock
    def test_find_task_project_id_not_found(self, client: DidaClient) -> None:
        respx.get("https://api.dida365.com/open/v1/project").mock(
            return_value=httpx.Response(
                200, json=[{"id": "p1", "name": "Work"}]
            )
        )
        respx.get("https://api.dida365.com/open/v1/project/p1/data").mock(
            return_value=httpx.Response(
                200,
                json={
                    "project": {"id": "p1", "name": "Work"},
                    "tasks": [{"id": "other", "title": "Other"}],
                },
            )
        )
        result = client.find_task_project_id("nonexistent")
        assert result is None

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

    # --- New method edge cases and payload verification ---

    @respx.mock
    def test_move_task_non_list_response(self, client: DidaClient) -> None:
        """move_task returns [] when API response is not a list."""
        respx.post("https://api.dida365.com/open/v1/task/move").mock(
            return_value=httpx.Response(200, json={})
        )
        result = client.move_task("t1", "p_from", "p_to")
        assert result == []

    @respx.mock
    def test_move_task_payload_structure(self, client: DidaClient) -> None:
        """Verify the exact payload sent to the API for move_task."""
        route = respx.post("https://api.dida365.com/open/v1/task/move").mock(
            return_value=httpx.Response(200, json=[{"taskId": "t1"}])
        )
        client.move_task("t1", "p_from", "p_to")
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert payload == [
            {"taskId": "t1", "fromProjectId": "p_from", "toProjectId": "p_to"}
        ]

    @respx.mock
    def test_move_task_api_error(self, client: DidaClient) -> None:
        """move_task raises ApiError on server error."""
        respx.post("https://api.dida365.com/open/v1/task/move").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ApiError, match="API 错误"):
            client.move_task("t1", "p1", "p2")

    @respx.mock
    def test_move_task_auth_error(self, client: DidaClient) -> None:
        """move_task raises AuthError on 401."""
        respx.post("https://api.dida365.com/open/v1/task/move").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(AuthError):
            client.move_task("t1", "p1", "p2")

    @respx.mock
    def test_filter_tasks_payload_uses_proiority(self, client: DidaClient) -> None:
        """Verify filter_tasks sends 'proiority' (misspelled) not 'priority'."""
        route = respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.filter_tasks(priority=[5, 3])
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert "proiority" in payload
        assert "priority" not in payload
        assert payload["proiority"] == [5, 3]

    @respx.mock
    def test_filter_tasks_full_payload(self, client: DidaClient) -> None:
        """Verify filter_tasks sends all params with correct field names."""
        route = respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.filter_tasks(
            project_ids=["p1"],
            start_date="2026-03-01T00:00:00+0800",
            end_date="2026-03-31T23:59:00+0800",
            priority=[5],
            tags=["work", "urgent"],
            status=[0, 2],
        )
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert payload["projectIds"] == ["p1"]
        assert payload["startDate"] == "2026-03-01T00:00:00+0800"
        assert payload["endDate"] == "2026-03-31T23:59:00+0800"
        assert payload["proiority"] == [5]
        assert payload["tag"] == ["work", "urgent"]
        assert payload["status"] == [0, 2]

    @respx.mock
    def test_filter_tasks_non_list_response(self, client: DidaClient) -> None:
        """filter_tasks returns [] when API response is not a list."""
        respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(200, json={})
        )
        tasks = client.filter_tasks(project_ids=["p1"])
        assert tasks == []

    @respx.mock
    def test_filter_tasks_api_error(self, client: DidaClient) -> None:
        """filter_tasks raises ApiError on server error."""
        respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        with pytest.raises(ApiError):
            client.filter_tasks()

    @respx.mock
    def test_list_completed_tasks_full_payload(self, client: DidaClient) -> None:
        """Verify list_completed_tasks sends all params with correct field names."""
        route = respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.list_completed_tasks(
            project_ids=["p1", "p2"],
            start_date="2026-03-01T00:00:00+0800",
            end_date="2026-03-31T23:59:00+0800",
        )
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert payload["projectIds"] == ["p1", "p2"]
        assert payload["startDate"] == "2026-03-01T00:00:00+0800"
        assert payload["endDate"] == "2026-03-31T23:59:00+0800"

    @respx.mock
    def test_list_completed_tasks_non_list_response(self, client: DidaClient) -> None:
        """list_completed_tasks returns [] when API response is not a list."""
        respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(200, json={})
        )
        tasks = client.list_completed_tasks(project_ids=["p1"])
        assert tasks == []

    @respx.mock
    def test_list_completed_tasks_api_error(self, client: DidaClient) -> None:
        """list_completed_tasks raises ApiError on server error."""
        respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        with pytest.raises(ApiError):
            client.list_completed_tasks()

    @respx.mock
    def test_filter_tasks_empty_payload_when_no_params(self, client: DidaClient) -> None:
        """filter_tasks sends empty payload when no params provided."""
        route = respx.post("https://api.dida365.com/open/v1/task/filter").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.filter_tasks()
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert payload == {}

    @respx.mock
    def test_list_completed_tasks_empty_payload(self, client: DidaClient) -> None:
        """list_completed_tasks sends empty payload when no params provided."""
        route = respx.post("https://api.dida365.com/open/v1/task/completed").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.list_completed_tasks()
        request = route.calls.last.request
        import json
        payload = json.loads(request.content)
        assert payload == {}
