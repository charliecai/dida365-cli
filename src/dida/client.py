"""HTTP client for Dida365 Open API v1."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from dida.auth import get_access_token, refresh_access_token
from dida.models import Project, ProjectData, Task

logger = logging.getLogger(__name__)

# Dida365 Open API base URL
BASE_URL = "https://api.dida365.com/open/v1"

# HTTP client configuration
TIMEOUT = 30
MAX_RETRIES = 3


class ApiError(Exception):
    """Error raised when API call fails."""

    def __init__(self, message: str, status_code: int = 0, code: str = "API_ERROR") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class AuthError(ApiError):
    """Error raised when authentication fails."""

    def __init__(self, message: str = "认证失败，请运行 dida auth login") -> None:
        super().__init__(message, status_code=401, code="AUTH_ERROR")


class DidaClient:
    """HTTP client for Dida365 Open API v1.

    Handles authentication, retries, and error handling.
    """

    def __init__(self) -> None:
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with auth headers."""
        token = get_access_token()
        if token is None:
            raise AuthError()

        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=BASE_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=TIMEOUT,
            )
        else:
            self._client.headers["Authorization"] = f"Bearer {token}"
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        retry_count: int = 0,
    ) -> Any:
        """Make an API request with retry and auth refresh logic."""
        client = self._get_client()

        try:
            response = client.request(method, path, json=json)
        except httpx.TimeoutException as e:
            if retry_count < MAX_RETRIES:
                logger.debug("Request timeout, retrying (%d/%d)", retry_count + 1, MAX_RETRIES)
                return self._request(method, path, json=json, retry_count=retry_count + 1)
            msg = "网络请求超时，请检查网络连接后重试"
            raise ApiError(msg, code="TIMEOUT") from e
        except httpx.HTTPError as e:
            if retry_count < MAX_RETRIES:
                return self._request(method, path, json=json, retry_count=retry_count + 1)
            msg = f"网络请求失败: {e}"
            raise ApiError(msg, code="NETWORK_ERROR") from e

        # Handle 401: try token refresh once
        if response.status_code == 401:
            if retry_count == 0:
                logger.debug("Got 401, attempting token refresh")
                new_token_data = refresh_access_token()
                if new_token_data:
                    # Close old client to force recreation with new token
                    self.close()
                    return self._request(method, path, json=json, retry_count=retry_count + 1)
            raise AuthError()

        if response.status_code >= 400:
            msg = f"API 错误 (HTTP {response.status_code}): {response.text}"
            raise ApiError(msg, status_code=response.status_code)

        # Some endpoints return empty body (204 No Content, or 200 with no body)
        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None

    # --- Project endpoints ---

    def list_projects(self) -> list[Project]:
        """Get all projects. GET /project"""
        data = self._request("GET", "/project")
        return [Project.from_dict(p) for p in data]

    def get_project(self, project_id: str) -> Project:
        """Get a single project. GET /project/{id}"""
        data = self._request("GET", f"/project/{project_id}")
        return Project.from_dict(data)

    def get_project_data(self, project_id: str) -> ProjectData:
        """Get project with tasks. GET /project/{id}/data"""
        data = self._request("GET", f"/project/{project_id}/data")
        return ProjectData.from_dict(data)

    def create_project(self, project: Project) -> Project:
        """Create a new project. POST /project"""
        data = self._request("POST", "/project", json=project.to_create_dict())
        return Project.from_dict(data)

    def update_project(self, project_id: str, project: Project) -> Project:
        """Update an existing project. POST /project/{id}"""
        data = self._request("POST", f"/project/{project_id}", json=project.to_update_dict())
        return Project.from_dict(data)

    def delete_project(self, project_id: str) -> None:
        """Delete a project. DELETE /project/{id}"""
        self._request("DELETE", f"/project/{project_id}")

    # --- Task endpoints ---

    def get_task(self, project_id: str, task_id: str) -> Task:
        """Get a single task. GET /project/{pid}/task/{tid}"""
        data = self._request("GET", f"/project/{project_id}/task/{task_id}")
        return Task.from_dict(data)

    def create_task(self, task: Task) -> Task:
        """Create a new task. POST /task"""
        data = self._request("POST", "/task", json=task.to_create_dict())
        return Task.from_dict(data)

    def update_task(self, task: Task) -> Task:
        """Update an existing task. POST /task/{id}"""
        data = self._request("POST", f"/task/{task.id}", json=task.to_update_dict())
        return Task.from_dict(data)

    def complete_task(self, project_id: str, task_id: str) -> None:
        """Mark a task as complete. POST /project/{pid}/task/{tid}/complete"""
        self._request("POST", f"/project/{project_id}/task/{task_id}/complete")

    def delete_task(self, project_id: str, task_id: str) -> None:
        """Delete a task. DELETE /project/{pid}/task/{tid}"""
        self._request("DELETE", f"/project/{project_id}/task/{task_id}")

    def batch_create_tasks(self, tasks: list[Task]) -> list[Task]:
        """Batch create tasks. POST /batch/task"""
        payload = [t.to_create_dict() for t in tasks]
        data = self._request("POST", "/batch/task", json=payload)
        if isinstance(data, list):
            return [Task.from_dict(t) for t in data]
        return []

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

    # --- Helper methods ---

    def find_project_by_name(self, name: str) -> list[Project]:
        """Find projects by name (case-insensitive substring match)."""
        projects = self.list_projects()
        name_lower = name.lower()
        return [p for p in projects if name_lower in p.name.lower()]

    def find_task_project_id(self, task_id: str) -> str | None:
        """Find the project ID for a given task by searching all projects.

        The Open API doesn't have a direct "get task by ID" endpoint,
        so we need to search through projects.
        """
        projects = self.list_projects()
        for project in projects:
            project_data = self.get_project_data(project.id)
            for task in project_data.tasks:
                if task.id == task_id:
                    return project.id
        return None
