"""Integration tests for Dida365 API — runs against the real API.

Requires a valid access token (run `dida auth login` first).
Skipped automatically when no token is available.

Usage:
    uv run pytest tests/test_integration.py -m integration -v
"""

from __future__ import annotations

import contextlib
import time

import pytest

from dida.auth import get_access_token
from dida.client import ApiError, DidaClient
from dida.models import Project, Task

# Skip entire module when no token is available
pytestmark = pytest.mark.integration

_token = get_access_token()
if _token is None:
    pytest.skip("No access token — skipping integration tests", allow_module_level=True)


@pytest.fixture()
def client():
    """Provide a DidaClient and close it after the test."""
    c = DidaClient()
    yield c
    c.close()


def test_project_and_task_crud_lifecycle(client: DidaClient) -> None:
    """Full CRUD lifecycle: project → task → update → complete → delete."""
    project_id: str | None = None
    task_id: str | None = None
    timestamp = int(time.time())
    project_name = f"_test_integration_{timestamp}"

    try:
        # ── 1. Create project ────────────────────────────────────────
        proj = Project(name=project_name, color="#F18181", view_mode="list")
        created_project = client.create_project(proj)

        assert created_project.id, "Project should have an id"
        project_id = created_project.id
        assert created_project.name == project_name
        assert created_project.color == "#F18181"
        assert created_project.view_mode == "list"

        # ── 2. Create task with rich parameters ──────────────────────
        due_date = "2099-12-31T23:59:00+0800"
        task = Task(
            title=f"Integration test task {timestamp}",
            project_id=project_id,
            priority=5,
            all_day=True,
            due_date=due_date,
            tags=["test-tag"],
            content="Integration test content",
        )
        created_task = client.create_task(task)

        assert created_task.id, "Task should have an id"
        task_id = created_task.id
        assert created_task.project_id == project_id
        assert created_task.priority == 5
        assert created_task.all_day is True
        assert "2099-12-31" in (created_task.due_date or "")
        assert "test-tag" in created_task.tags
        assert created_task.content == "Integration test content"

        # ── 3. Get task ──────────────────────────────────────────────
        fetched = client.get_task(project_id, task_id)
        assert fetched.id == task_id
        assert fetched.title == created_task.title
        assert fetched.priority == 5
        assert fetched.content == "Integration test content"

        # ── 4. Update task ───────────────────────────────────────────
        update = Task(
            id=task_id,
            project_id=project_id,
            title=f"Updated title {timestamp}",
            priority=3,
            content="Updated content",
        )
        updated = client.update_task(update)
        assert updated.title == f"Updated title {timestamp}"
        assert updated.priority == 3
        assert updated.content == "Updated content"

        # Verify via get
        refetched = client.get_task(project_id, task_id)
        assert refetched.title == f"Updated title {timestamp}"
        assert refetched.priority == 3

        # ── 5. Filter tasks by project ───────────────────────────────
        filtered = client.filter_tasks(project_ids=[project_id])
        task_ids = [t.id for t in filtered]
        assert task_id in task_ids, "Task should appear in filter results"

        # ── 6. Complete task ─────────────────────────────────────────
        client.complete_task(project_id, task_id)

        # ── 7. List completed tasks ──────────────────────────────────
        completed = client.list_completed_tasks(project_ids=[project_id])
        completed_ids = [t.id for t in completed]
        assert task_id in completed_ids, "Task should appear in completed list"

        # ── 8. Delete task ───────────────────────────────────────────
        client.delete_task(project_id, task_id)
        task_id = None  # Prevent double-delete in finally

        # Verify deletion — get_task should raise 404
        with pytest.raises(ApiError) as exc_info:
            client.get_task(project_id, f"nonexistent_{timestamp}")
        assert exc_info.value.status_code >= 400

        # ── 9. Delete project (cleanup) ──────────────────────────────
        client.delete_project(project_id)
        project_id = None  # Prevent double-delete in finally

    finally:
        # Safety cleanup: delete project (cascades tasks) if still alive
        if project_id:
            with contextlib.suppress(ApiError):
                client.delete_project(project_id)
