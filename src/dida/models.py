"""Data models for Dida365 Open API v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class TaskPriority(IntEnum):
    """Task priority levels mapping to Dida365 API values."""

    NONE = 0
    LOW = 1
    MEDIUM = 3
    HIGH = 5

    @classmethod
    def from_str(cls, value: str) -> TaskPriority:
        """Parse priority from string name."""
        mapping = {
            "none": cls.NONE,
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "mid": cls.MEDIUM,
            "high": cls.HIGH,
        }
        result = mapping.get(value.lower())
        if result is None:
            valid = ", ".join(mapping.keys())
            msg = f"Invalid priority '{value}'. Valid values: {valid}"
            raise ValueError(msg)
        return result

    def to_label(self) -> str:
        """Return Chinese label for display."""
        labels = {0: "无", 1: "低", 3: "中", 5: "高"}
        return labels.get(self.value, "无")


class TaskStatus(IntEnum):
    """Task status values from Dida365 API."""

    NORMAL = 0
    COMPLETED = 2


@dataclass
class ChecklistItem:
    """A subtask/checklist item within a task."""

    id: str = ""
    title: str = ""
    status: int = 0
    sort_order: int = 0
    start_date: str | None = None
    is_all_day: bool = False
    time_zone: str = ""
    completed_time: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ChecklistItem:
        """Create ChecklistItem from API response dict."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            status=data.get("status", 0),
            sort_order=data.get("sortOrder", 0),
            start_date=data.get("startDate"),
            is_all_day=data.get("isAllDay", False),
            time_zone=data.get("timeZone", ""),
            completed_time=data.get("completedTime"),
        )

    def to_dict(self) -> dict:
        """Convert to API request dict."""
        result: dict = {"title": self.title, "status": self.status}
        if self.id:
            result["id"] = self.id
        return result


@dataclass
class Task:
    """A Dida365 task."""

    id: str = ""
    project_id: str = ""
    title: str = ""
    content: str = ""
    desc: str = ""
    all_day: bool = False
    start_date: str | None = None
    due_date: str | None = None
    time_zone: str = "Asia/Shanghai"
    reminders: list[str] = field(default_factory=list)
    repeat: str = ""
    priority: int = 0
    status: int = 0
    completed_time: str | None = None
    sort_order: int = 0
    items: list[ChecklistItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Create Task from API response dict."""
        items_data = data.get("items", [])
        items = [ChecklistItem.from_dict(item) for item in items_data] if items_data else []
        return cls(
            id=data.get("id", ""),
            project_id=data.get("projectId", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            desc=data.get("desc", ""),
            all_day=data.get("allDay", False),
            start_date=data.get("startDate"),
            due_date=data.get("dueDate"),
            time_zone=data.get("timeZone", "Asia/Shanghai"),
            reminders=data.get("reminders", []),
            repeat=data.get("repeat", ""),
            priority=data.get("priority", 0),
            status=data.get("status", 0),
            completed_time=data.get("completedTime"),
            sort_order=data.get("sortOrder", 0),
            items=items,
        )

    def to_create_dict(self) -> dict:
        """Convert to API request dict for task creation."""
        result: dict = {"title": self.title}
        if self.project_id:
            result["projectId"] = self.project_id
        if self.content:
            result["content"] = self.content
        if self.desc:
            result["desc"] = self.desc
        if self.all_day:
            result["allDay"] = self.all_day
        if self.start_date:
            result["startDate"] = self.start_date
        if self.due_date:
            result["dueDate"] = self.due_date
        if self.time_zone:
            result["timeZone"] = self.time_zone
        if self.reminders:
            result["reminders"] = self.reminders
        if self.repeat:
            result["repeat"] = self.repeat
        if self.priority:
            result["priority"] = self.priority
        if self.items:
            result["items"] = [item.to_dict() for item in self.items]
        return result

    def to_update_dict(self) -> dict:
        """Convert to API request dict for task update. Includes id and projectId."""
        result: dict = {"id": self.id, "projectId": self.project_id}
        if self.title:
            result["title"] = self.title
        if self.content:
            result["content"] = self.content
        if self.priority is not None:
            result["priority"] = self.priority
        if self.due_date:
            result["dueDate"] = self.due_date
        if self.start_date:
            result["startDate"] = self.start_date
        return result

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict for --json output."""
        result = {
            "id": self.id,
            "projectId": self.project_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
        }
        if self.content:
            result["content"] = self.content
        if self.due_date:
            result["dueDate"] = self.due_date
        if self.start_date:
            result["startDate"] = self.start_date
        if self.completed_time:
            result["completedTime"] = self.completed_time
        if self.items:
            result["items"] = [{"title": item.title, "status": item.status} for item in self.items]
        return result

    @property
    def priority_label(self) -> str:
        """Human-readable priority label."""
        return TaskPriority(self.priority).to_label() if self.priority in (0, 1, 3, 5) else "无"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def due_date_display(self) -> str:
        """Format due date for display. Returns empty string if no due date."""
        if not self.due_date:
            return ""
        try:
            dt = datetime.fromisoformat(self.due_date.replace("+0000", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return self.due_date


@dataclass
class Project:
    """A Dida365 project (task list)."""

    id: str = ""
    name: str = ""
    color: str = ""
    sort_order: int = 0
    closed: bool = False
    group_id: str = ""
    view_mode: str | None = None
    kind: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        """Create Project from API response dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            color=data.get("color", ""),
            sort_order=data.get("sortOrder", 0),
            closed=data.get("closed", False),
            group_id=data.get("groupId", ""),
            view_mode=data.get("viewMode"),
            kind=data.get("kind"),
        )

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict for --json output."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "closed": self.closed,
        }


@dataclass
class ProjectData:
    """A project with its associated tasks."""

    project: Project
    tasks: list[Task] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ProjectData:
        """Create ProjectData from API response dict."""
        project = Project.from_dict(data.get("project", data))
        tasks_data = data.get("tasks", [])
        tasks = [Task.from_dict(t) for t in tasks_data]
        return cls(project=project, tasks=tasks)
