"""Output formatting utilities for CLI and JSON modes."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from dida.models import Project, ProjectData, Task, TaskPriority

console = Console()
err_console = Console(stderr=True)

# Priority display styles
PRIORITY_STYLES = {
    5: ("[red]高[/red]", "!!"),
    3: ("[yellow]中[/yellow]", "!"),
    1: ("[blue]低[/blue]", "."),
    0: ("[dim]无[/dim]", " "),
}


def output_json(data: Any) -> None:
    """Output data as JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(message: str, code: str = "ERROR") -> None:
    """Output error message to stderr."""
    err_console.print(f"[red]错误:[/red] {message}")


def output_error_json(message: str, code: str = "ERROR") -> None:
    """Output error as JSON to stdout."""
    output_json({"error": message, "code": code})


def output_success(message: str) -> None:
    """Output success message to stderr for human-readable mode."""
    err_console.print(f"[green]✓[/green] {message}")


def display_tasks(tasks: list[Task], *, as_json: bool = False) -> None:
    """Display a list of tasks as table or JSON."""
    if as_json:
        output_json({"success": True, "data": [t.to_json_dict() for t in tasks]})
        return

    if not tasks:
        console.print("[dim]没有任务[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", max_width=24)
    table.add_column("优先级", justify="center", width=6)
    table.add_column("标题", min_width=20)
    table.add_column("截止日期", width=16)
    table.add_column("状态", justify="center", width=6)

    for task in tasks:
        style, _icon = PRIORITY_STYLES.get(task.priority, PRIORITY_STYLES[0])
        status = "[green]✓[/green]" if task.is_completed else "[dim]○[/dim]"
        due = task.due_date_display or "[dim]-[/dim]"

        table.add_row(
            task.id[:12] + "..." if len(task.id) > 15 else task.id,
            style,
            task.title,
            due,
            status,
        )

    console.print(table)


def display_projects(projects: list[Project], *, as_json: bool = False) -> None:
    """Display a list of projects as table or JSON."""
    if as_json:
        output_json({"success": True, "data": [p.to_json_dict() for p in projects]})
        return

    if not projects:
        console.print("[dim]没有项目[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", max_width=24)
    table.add_column("名称", min_width=15)
    table.add_column("状态", justify="center", width=6)

    for project in projects:
        status = "[dim]已关闭[/dim]" if project.closed else "[green]活跃[/green]"
        table.add_row(project.id, project.name, status)

    console.print(table)


def display_project_data(project_data: ProjectData, *, as_json: bool = False) -> None:
    """Display project details with its tasks."""
    if as_json:
        data = {
            "success": True,
            "data": {
                "project": project_data.project.to_json_dict(),
                "tasks": [t.to_json_dict() for t in project_data.tasks],
            },
        }
        output_json(data)
        return

    console.print(f"\n[bold]{project_data.project.name}[/bold]")
    console.print(f"[dim]ID: {project_data.project.id}[/dim]\n")
    display_tasks(project_data.tasks)


def display_task(task: Task, *, as_json: bool = False, action: str = "已创建") -> None:
    """Display a single task result."""
    if as_json:
        output_json({"success": True, "data": task.to_json_dict()})
        return

    priority_label = TaskPriority(task.priority).to_label() if task.priority in (0, 1, 3, 5) else ""
    due = f" 截止: {task.due_date_display}" if task.due_date_display else ""
    priority_str = f" [{priority_label}优先级]" if task.priority > 0 else ""
    output_success(f"{action}: {task.title}{priority_str}{due}")
