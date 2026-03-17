"""Tests for dida.models module."""

from dida.models import (
    ChecklistItem,
    Column,
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
            "desc": "A description",
            "tags": ["work", "urgent"],
            "isAllDay": True,
            "startDate": "2026-03-01T00:00:00+0800",
            "priority": 5,
            "status": 2,
            "dueDate": "2026-03-01T15:00:00+0800",
            "timeZone": "America/New_York",
            "reminders": ["TRIGGER:PT0S"],
            "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
            "sortOrder": 42,
            "completedTime": "2026-03-02T10:00:00+0800",
            "items": [
                {"id": "item1", "title": "Subtask 1", "status": 0},
                {"id": "item2", "title": "Subtask 2", "status": 2},
            ],
        }
        task = Task.from_dict(data)
        assert task.project_id == "proj1"
        assert task.content == "Some content"
        assert task.desc == "A description"
        assert task.tags == ["work", "urgent"]
        assert task.all_day is True
        assert task.start_date == "2026-03-01T00:00:00+0800"
        assert task.time_zone == "America/New_York"
        assert task.reminders == ["TRIGGER:PT0S"]
        assert task.repeat_flag == "RRULE:FREQ=DAILY;INTERVAL=1"
        assert task.sort_order == 42
        assert task.completed_time == "2026-03-02T10:00:00+0800"
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

    def test_to_create_dict_all_fields(self) -> None:
        task = Task(
            title="Full",
            project_id="p1",
            content="notes",
            desc="desc",
            tags=["a", "b"],
            all_day=True,
            start_date="2026-03-01",
            due_date="2026-03-10",
            time_zone="UTC",
            reminders=["TRIGGER:PT0S"],
            repeat_flag="RRULE:FREQ=DAILY;INTERVAL=1",
            priority=5,
            sort_order=10,
            items=[ChecklistItem(title="Sub1")],
        )
        result = task.to_create_dict()
        assert result["projectId"] == "p1"
        assert result["content"] == "notes"
        assert result["desc"] == "desc"
        assert result["tags"] == ["a", "b"]
        assert result["isAllDay"] is True
        assert result["startDate"] == "2026-03-01"
        assert result["dueDate"] == "2026-03-10"
        assert result["timeZone"] == "UTC"
        assert result["reminders"] == ["TRIGGER:PT0S"]
        assert result["repeatFlag"] == "RRULE:FREQ=DAILY;INTERVAL=1"
        assert result["priority"] == 5
        assert result["sortOrder"] == 10
        assert len(result["items"]) == 1

    def test_to_update_dict(self) -> None:
        task = Task(
            id="t1",
            project_id="p1",
            title="Updated",
            content="new content",
            desc="new desc",
            tags=["x"],
            due_date="2026-04-01",
            priority=3,
        )
        result = task.to_update_dict()
        assert result["id"] == "t1"
        assert result["projectId"] == "p1"
        assert result["title"] == "Updated"
        assert result["content"] == "new content"
        assert result["desc"] == "new desc"
        assert result["tags"] == ["x"]
        assert result["dueDate"] == "2026-04-01"
        assert result["priority"] == 3

    def test_to_json_dict(self) -> None:
        task = Task(id="abc", project_id="proj1", title="Test", priority=5, status=0)
        result = task.to_json_dict()
        assert result["id"] == "abc"
        assert result["title"] == "Test"
        assert result["priority"] == 5

    def test_to_json_dict_with_optional_fields(self) -> None:
        task = Task(
            id="t1",
            project_id="p1",
            title="Full",
            content="notes",
            desc="desc",
            tags=["a"],
            all_day=True,
            due_date="2026-03-10",
            start_date="2026-03-01",
            time_zone="UTC",
            reminders=["TRIGGER:PT0S"],
            repeat_flag="RRULE:FREQ=DAILY",
            completed_time="2026-03-11",
            sort_order=5,
            items=[ChecklistItem(id="i1", title="Sub", status=0)],
        )
        result = task.to_json_dict()
        assert result["content"] == "notes"
        assert result["desc"] == "desc"
        assert result["tags"] == ["a"]
        assert result["isAllDay"] is True
        assert result["dueDate"] == "2026-03-10"
        assert result["startDate"] == "2026-03-01"
        assert result["timeZone"] == "UTC"
        assert result["reminders"] == ["TRIGGER:PT0S"]
        assert result["repeatFlag"] == "RRULE:FREQ=DAILY"
        assert result["completedTime"] == "2026-03-11"
        assert result["sortOrder"] == 5
        assert len(result["items"]) == 1

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

    def test_start_date_display(self) -> None:
        task = Task(start_date="2026-03-01T09:00:00+00:00")
        assert "2026-03-01" in task.start_date_display

    def test_start_date_display_empty(self) -> None:
        task = Task()
        assert task.start_date_display == ""


class TestProject:
    """Tests for Project dataclass."""

    def test_from_dict(self) -> None:
        data = {
            "id": "proj1",
            "name": "Work",
            "color": "#ff0000",
            "closed": False,
            "sortOrder": 10,
            "groupId": "g1",
            "viewMode": "kanban",
            "permission": "rw",
            "kind": "TASK",
        }
        project = Project.from_dict(data)
        assert project.id == "proj1"
        assert project.name == "Work"
        assert project.sort_order == 10
        assert project.group_id == "g1"
        assert project.view_mode == "kanban"
        assert project.permission == "rw"
        assert project.kind == "TASK"
        assert not project.closed

    def test_to_create_dict(self) -> None:
        proj = Project(name="New", color="#abc", view_mode="list", kind="TASK", sort_order=5)
        result = proj.to_create_dict()
        assert result["name"] == "New"
        assert result["color"] == "#abc"
        assert result["viewMode"] == "list"
        assert result["kind"] == "TASK"
        assert result["sortOrder"] == 5

    def test_to_create_dict_minimal(self) -> None:
        proj = Project(name="Simple")
        result = proj.to_create_dict()
        assert result == {"name": "Simple"}

    def test_to_update_dict(self) -> None:
        proj = Project(name="Updated", color="#000", view_mode="kanban", kind="NOTE", sort_order=3)
        result = proj.to_update_dict()
        assert result["name"] == "Updated"
        assert result["color"] == "#000"
        assert result["viewMode"] == "kanban"
        assert result["kind"] == "NOTE"
        assert result["sortOrder"] == 3

    def test_to_update_dict_empty(self) -> None:
        proj = Project()
        result = proj.to_update_dict()
        assert result == {}

    def test_to_json_dict(self) -> None:
        project = Project(id="proj1", name="Work", color="#ff0000")
        result = project.to_json_dict()
        assert result["id"] == "proj1"
        assert result["name"] == "Work"
        assert result["color"] == "#ff0000"
        assert result["closed"] is False

    def test_to_json_dict_with_optional_fields(self) -> None:
        project = Project(
            id="p1", name="Full", sort_order=5, group_id="g1",
            view_mode="kanban", permission="rw", kind="TASK",
        )
        result = project.to_json_dict()
        assert result["sortOrder"] == 5
        assert result["groupId"] == "g1"
        assert result["viewMode"] == "kanban"
        assert result["permission"] == "rw"
        assert result["kind"] == "TASK"


class TestColumn:
    """Tests for Column dataclass."""

    def test_from_dict(self) -> None:
        data = {"id": "c1", "projectId": "p1", "name": "To Do", "sortOrder": 0}
        col = Column.from_dict(data)
        assert col.id == "c1"
        assert col.project_id == "p1"
        assert col.name == "To Do"
        assert col.sort_order == 0

    def test_to_json_dict(self) -> None:
        col = Column(id="c1", project_id="p1", name="Done", sort_order=2)
        result = col.to_json_dict()
        assert result == {"id": "c1", "projectId": "p1", "name": "Done", "sortOrder": 2}


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

    def test_from_dict_with_columns(self) -> None:
        data = {
            "project": {"id": "p1", "name": "Kanban"},
            "tasks": [],
            "columns": [
                {"id": "c1", "projectId": "p1", "name": "To Do", "sortOrder": 0},
                {"id": "c2", "projectId": "p1", "name": "Done", "sortOrder": 1},
            ],
        }
        pd = ProjectData.from_dict(data)
        assert len(pd.columns) == 2
        assert pd.columns[0].name == "To Do"
        assert pd.columns[1].name == "Done"


class TestChecklistItem:
    """Tests for ChecklistItem dataclass."""

    def test_from_dict(self) -> None:
        data = {"id": "item1", "title": "Subtask", "status": 0}
        item = ChecklistItem.from_dict(data)
        assert item.id == "item1"
        assert item.title == "Subtask"

    def test_from_dict_full(self) -> None:
        data = {
            "id": "item1",
            "title": "Sub",
            "status": 2,
            "sortOrder": 5,
            "startDate": "2026-03-01",
            "isAllDay": True,
            "timeZone": "UTC",
            "completedTime": "2026-03-02",
        }
        item = ChecklistItem.from_dict(data)
        assert item.sort_order == 5
        assert item.start_date == "2026-03-01"
        assert item.is_all_day is True
        assert item.time_zone == "UTC"
        assert item.completed_time == "2026-03-02"

    def test_to_dict(self) -> None:
        item = ChecklistItem(id="item1", title="Subtask", status=0)
        result = item.to_dict()
        assert result == {"id": "item1", "title": "Subtask", "status": 0}

    def test_to_dict_with_optional_fields(self) -> None:
        item = ChecklistItem(
            id="i1", title="Sub", status=0, sort_order=3,
            start_date="2026-03-01", is_all_day=True,
            time_zone="UTC", completed_time="2026-03-02",
        )
        result = item.to_dict()
        assert result["sortOrder"] == 3
        assert result["startDate"] == "2026-03-01"
        assert result["isAllDay"] is True
        assert result["timeZone"] == "UTC"
        assert result["completedTime"] == "2026-03-02"
