"""Tests for dida.models module."""

from dida.models import (
    ChecklistItem,
    Project,
    ProjectData,
    Task,
    TaskPriority,
    TaskStatus,
)


class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_from_str_valid(self) -> None:
        assert TaskPriority.from_str("none") == TaskPriority.NONE
        assert TaskPriority.from_str("low") == TaskPriority.LOW
        assert TaskPriority.from_str("medium") == TaskPriority.MEDIUM
        assert TaskPriority.from_str("mid") == TaskPriority.MEDIUM
        assert TaskPriority.from_str("high") == TaskPriority.HIGH

    def test_from_str_case_insensitive(self) -> None:
        assert TaskPriority.from_str("HIGH") == TaskPriority.HIGH
        assert TaskPriority.from_str("Low") == TaskPriority.LOW

    def test_from_str_invalid(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Invalid priority"):
            TaskPriority.from_str("urgent")

    def test_to_label(self) -> None:
        assert TaskPriority.NONE.to_label() == "无"
        assert TaskPriority.LOW.to_label() == "低"
        assert TaskPriority.MEDIUM.to_label() == "中"
        assert TaskPriority.HIGH.to_label() == "高"

    def test_int_values(self) -> None:
        assert TaskPriority.NONE == 0
        assert TaskPriority.LOW == 1
        assert TaskPriority.MEDIUM == 3
        assert TaskPriority.HIGH == 5


class TestTask:
    """Tests for Task dataclass."""

    def test_from_dict_minimal(self) -> None:
        data = {"id": "abc123", "title": "Test task"}
        task = Task.from_dict(data)
        assert task.id == "abc123"
        assert task.title == "Test task"
        assert task.priority == 0
        assert task.status == 0

    def test_from_dict_full(self) -> None:
        data = {
            "id": "abc123",
            "projectId": "proj1",
            "title": "Full task",
            "content": "Some content",
            "priority": 5,
            "status": 2,
            "dueDate": "2026-03-01T15:00:00+0800",
            "items": [
                {"id": "item1", "title": "Subtask 1", "status": 0},
                {"id": "item2", "title": "Subtask 2", "status": 2},
            ],
        }
        task = Task.from_dict(data)
        assert task.project_id == "proj1"
        assert task.priority == 5
        assert task.is_completed
        assert len(task.items) == 2
        assert task.items[0].title == "Subtask 1"

    def test_to_create_dict(self) -> None:
        task = Task(title="New task", priority=3, project_id="proj1")
        result = task.to_create_dict()
        assert result["title"] == "New task"
        assert result["priority"] == 3
        assert result["projectId"] == "proj1"

    def test_to_create_dict_minimal(self) -> None:
        task = Task(title="Simple task")
        result = task.to_create_dict()
        assert result["title"] == "Simple task"
        assert "timeZone" in result  # Default timezone is always included

    def test_to_json_dict(self) -> None:
        task = Task(id="abc", project_id="proj1", title="Test", priority=5, status=0)
        result = task.to_json_dict()
        assert result["id"] == "abc"
        assert result["title"] == "Test"
        assert result["priority"] == 5

    def test_priority_label(self) -> None:
        task = Task(priority=5)
        assert task.priority_label == "高"

    def test_is_completed(self) -> None:
        assert not Task(status=TaskStatus.NORMAL).is_completed
        assert Task(status=TaskStatus.COMPLETED).is_completed

    def test_due_date_display(self) -> None:
        task = Task(due_date="2026-03-01T15:00:00+00:00")
        assert "2026-03-01" in task.due_date_display

    def test_due_date_display_empty(self) -> None:
        task = Task()
        assert task.due_date_display == ""


class TestProject:
    """Tests for Project dataclass."""

    def test_from_dict(self) -> None:
        data = {"id": "proj1", "name": "Work", "color": "#ff0000", "closed": False}
        project = Project.from_dict(data)
        assert project.id == "proj1"
        assert project.name == "Work"
        assert not project.closed

    def test_to_json_dict(self) -> None:
        project = Project(id="proj1", name="Work", color="#ff0000")
        result = project.to_json_dict()
        assert result == {"id": "proj1", "name": "Work", "color": "#ff0000", "closed": False}


class TestProjectData:
    """Tests for ProjectData dataclass."""

    def test_from_dict(self) -> None:
        data = {
            "project": {"id": "proj1", "name": "Work"},
            "tasks": [
                {"id": "t1", "title": "Task 1"},
                {"id": "t2", "title": "Task 2"},
            ],
        }
        pd = ProjectData.from_dict(data)
        assert pd.project.name == "Work"
        assert len(pd.tasks) == 2
        assert pd.tasks[0].title == "Task 1"


class TestChecklistItem:
    """Tests for ChecklistItem dataclass."""

    def test_from_dict(self) -> None:
        data = {"id": "item1", "title": "Subtask", "status": 0}
        item = ChecklistItem.from_dict(data)
        assert item.id == "item1"
        assert item.title == "Subtask"

    def test_to_dict(self) -> None:
        item = ChecklistItem(id="item1", title="Subtask", status=0)
        result = item.to_dict()
        assert result == {"id": "item1", "title": "Subtask", "status": 0}
