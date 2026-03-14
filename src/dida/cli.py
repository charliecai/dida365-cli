"""Dida CLI - Command line tool for Dida365 task management."""

from __future__ import annotations

import json
import platform
import shutil
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from dida.auth import delete_token, load_token, oauth_login
from dida.client import ApiError, AuthError, DidaClient
from dida.models import Task, TaskPriority
from dida.output import (
    display_project_data,
    display_projects,
    display_task,
    display_tasks,
    output_error,
    output_error_json,
    output_json,
    output_success,
)

app = typer.Typer(
    name="dida",
    help="滴答清单 (Dida365) CLI 工具",
    no_args_is_help=True,
)

auth_app = typer.Typer(help="认证管理", no_args_is_help=True)
task_app = typer.Typer(help="任务管理", no_args_is_help=True)
project_app = typer.Typer(help="项目管理", no_args_is_help=True)

app.add_typer(auth_app, name="auth")
app.add_typer(task_app, name="task")
app.add_typer(project_app, name="project")

console = Console()

# Common options
JsonOption = Annotated[bool, typer.Option("--json", help="输出 JSON 格式")]


def _get_client() -> DidaClient:
    """Get API client, exit with error if not authenticated."""
    return DidaClient()


def _handle_error(e: Exception, *, as_json: bool = False) -> None:
    """Handle API errors with appropriate output and exit code."""
    if isinstance(e, AuthError):
        if as_json:
            output_error_json(str(e), "AUTH_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=2)
    elif isinstance(e, ApiError):
        if as_json:
            output_error_json(str(e), e.code)
        else:
            output_error(str(e))
        raise typer.Exit(code=1)
    else:
        if as_json:
            output_error_json(str(e), "UNKNOWN_ERROR")
        else:
            output_error(f"未知错误: {e}")
        raise typer.Exit(code=1)


# ── Setup command ────────────────────────────────────────────────────


@app.command("setup")
def setup(
    as_json: JsonOption = False,
) -> None:
    """检查环境状态，引导初始化配置。"""
    checks: list[dict] = []
    all_ok = True

    # 1. Python version
    py_ver = platform.python_version()
    py_ok = sys.version_info >= (3, 12)
    checks.append({"name": "Python", "version": py_ver, "ok": py_ok})
    if not py_ok:
        all_ok = False

    # 2. uv available
    uv_path = shutil.which("uv")
    uv_ok = uv_path is not None
    checks.append({"name": "uv", "ok": uv_ok})
    if not uv_ok:
        all_ok = False

    # 3. dida CLI version
    from dida import __version__

    checks.append({"name": "dida CLI", "version": __version__, "ok": True})

    # 4. Auth status
    token_data = load_token()
    auth_ok = bool(token_data and token_data.get("access_token"))
    checks.append({"name": "认证状态", "ok": auth_ok})
    if not auth_ok:
        all_ok = False

    if as_json:
        output_json({"ok": all_ok, "checks": checks})
        if not all_ok:
            raise typer.Exit(code=1)
        return

    # Rich output
    for check in checks:
        status = "[green]✓[/green]" if check["ok"] else "[red]✗[/red]"
        version = f" ({check['version']})" if "version" in check else ""
        console.print(f"  {status} {check['name']}{version}")

    console.print()

    if not py_ok:
        output_error("需要 Python 3.12+")
    if not uv_ok:
        output_error("未找到 uv，请安装: https://docs.astral.sh/uv/")
    if not auth_ok:
        console.print("[yellow]未认证。请按以下步骤操作：[/yellow]")
        console.print("  1. 前往 https://developer.dida365.com/ 注册开发者应用")
        console.print("  2. 设置回调地址为 http://localhost:18365/callback")
        console.print("  3. 运行 [bold]dida auth login[/bold] 完成认证")

    if all_ok:
        output_success("环境就绪")
    else:
        raise typer.Exit(code=1)


# ── Auth commands ────────────────────────────────────────────────────


@auth_app.command("login")
def auth_login() -> None:
    """通过 OAuth 2.0 登录滴答清单。"""
    client_id = Prompt.ask("请输入 Client ID")
    client_secret = Prompt.ask("请输入 Client Secret")

    if not client_id or not client_secret:
        output_error("Client ID 和 Client Secret 不能为空")
        raise typer.Exit(code=1)

    console.print("[dim]正在打开浏览器进行授权...[/dim]")
    try:
        oauth_login(client_id, client_secret)
        output_success("认证成功")
    except RuntimeError as e:
        output_error(str(e))
        raise typer.Exit(code=1) from None


@auth_app.command("status")
def auth_status(
    as_json: JsonOption = False,
) -> None:
    """查看认证状态。"""
    token_data = load_token()
    if token_data and token_data.get("access_token"):
        if as_json:
            output_json({"authenticated": True})
        else:
            output_success("已认证")
    else:
        if as_json:
            output_json({"authenticated": False})
        else:
            output_error("未认证，请运行 dida auth login")
        raise typer.Exit(code=2)


@auth_app.command("logout")
def auth_logout() -> None:
    """登出并删除本地 Token。"""
    if delete_token():
        output_success("已登出，Token 已删除")
    else:
        output_error("未找到 Token 文件")


# ── Task commands ────────────────────────────────────────────────────


@task_app.command("add")
def task_add(
    title: Annotated[str, typer.Argument(help="任务标题")],
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    due: Annotated[
        str | None,
        typer.Option("--due", "-d", help="截止日期 (tomorrow, 2026-03-01, 2026-03-01T15:00)"),
    ] = None,
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容/备注")] = None,
    as_json: JsonOption = False,
) -> None:
    """创建新任务。"""
    client = _get_client()
    try:
        task = Task(title=title)

        # Parse priority
        if priority:
            task.priority = TaskPriority.from_str(priority).value

        # Parse due date
        if due:
            task.due_date = _parse_date(due)

        # Resolve project
        if project:
            project_id = _resolve_project_id(client, project)
            if project_id:
                task.project_id = project_id

        if content:
            task.content = content

        created = client.create_task(task)
        display_task(created, as_json=as_json, action="已创建")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    except ValueError as e:
        if as_json:
            output_error_json(str(e), "VALIDATION_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=1) from None
    finally:
        client.close()


@task_app.command("list")
def task_list(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    all_projects: Annotated[bool, typer.Option("--all", help="包含已关闭项目的任务")] = False,
    as_json: JsonOption = False,
) -> None:
    """查看任务列表。"""
    client = _get_client()
    try:
        if project:
            project_id = _resolve_project_id(client, project)
            if project_id is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_data = client.get_project_data(project_id)
            tasks = project_data.tasks
        else:
            # List tasks from all (or only active) projects
            projects = client.list_projects()
            if not all_projects:
                projects = [p for p in projects if not p.closed]
            tasks = []
            for p in projects:
                pd = client.get_project_data(p.id)
                tasks.extend(pd.tasks)

        # Sort: uncompleted first, then by priority desc, then by due date
        tasks.sort(key=lambda t: (t.is_completed, -t.priority, t.due_date or "9999"))
        display_tasks(tasks, as_json=as_json)
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


@task_app.command("update")
def task_update(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    title: Annotated[str | None, typer.Option("--title", "-t", help="新标题")] = None,
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    due: Annotated[str | None, typer.Option("--due", "-d", help="截止日期")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容")] = None,
    as_json: JsonOption = False,
) -> None:
    """更新任务。"""
    client = _get_client()
    try:
        # Find the task's project ID (skip lookup if provided)
        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        task = Task(id=task_id, project_id=pid)
        if title:
            task.title = title
        if priority:
            task.priority = TaskPriority.from_str(priority).value
        if due:
            task.due_date = _parse_date(due)
        if content:
            task.content = content

        updated = client.update_task(task)
        display_task(updated, as_json=as_json, action="已更新")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    except ValueError as e:
        if as_json:
            output_error_json(str(e), "VALIDATION_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=1) from None
    finally:
        client.close()


@task_app.command("done")
def task_done(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """完成任务。"""
    client = _get_client()
    try:
        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        client.complete_task(pid, task_id)
        if as_json:
            output_json({"success": True, "data": {"id": task_id, "status": "completed"}})
        else:
            output_success(f"已完成任务: {task_id}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


@task_app.command("delete")
def task_delete(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="跳过确认")] = False,
    as_json: JsonOption = False,
) -> None:
    """删除任务。"""
    client = _get_client()
    try:
        # Skip confirmation in JSON mode or with --yes
        if not as_json and not yes and not Confirm.ask(f"确认删除任务 {task_id}?"):
            console.print("[dim]已取消[/dim]")
            raise typer.Exit(code=0)

        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        client.delete_task(pid, task_id)
        if as_json:
            output_json({"success": True, "data": {"id": task_id, "status": "deleted"}})
        else:
            output_success(f"已删除任务: {task_id}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


@task_app.command("batch-add")
def task_batch_add(
    as_json: JsonOption = False,
) -> None:
    """批量创建任务 (从 stdin 读取 JSON)。

    JSON 格式: [{"title": "任务1", "priority": 5}, {"title": "任务2"}]
    """
    client = _get_client()
    try:
        raw = sys.stdin.read()
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            msg = f"JSON 解析失败: {e}"
            if as_json:
                output_error_json(msg, "VALIDATION_ERROR")
            else:
                output_error(msg)
            raise typer.Exit(code=1) from None

        if not isinstance(items, list):
            msg = "输入必须是 JSON 数组"
            if as_json:
                output_error_json(msg, "VALIDATION_ERROR")
            else:
                output_error(msg)
            raise typer.Exit(code=1)

        tasks = [Task.from_dict(item) for item in items]
        created = client.batch_create_tasks(tasks)
        if as_json:
            output_json(
                {
                    "success": True,
                    "data": [t.to_json_dict() for t in created],
                    "count": len(created),
                }
            )
        else:
            output_success(f"已批量创建 {len(created)} 个任务")
            for t in created:
                console.print(f"  - {t.title}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


# ── Project commands ─────────────────────────────────────────────────


@project_app.command("list")
def project_list(
    as_json: JsonOption = False,
) -> None:
    """查看所有项目。"""
    client = _get_client()
    try:
        projects = client.list_projects()
        display_projects(projects, as_json=as_json)
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


@project_app.command("show")
def project_show(
    name_or_id: Annotated[str, typer.Argument(help="项目名称或 ID")],
    as_json: JsonOption = False,
) -> None:
    """查看项目详情及任务。"""
    client = _get_client()
    try:
        # Try as ID first (only if it looks like an ID, not a human name)
        try:
            project_data = client.get_project_data(name_or_id)
            # API may return 200 with empty data for invalid IDs — verify
            if project_data.project.id:
                display_project_data(project_data, as_json=as_json)
                return
        except ApiError:
            pass

        # Try fuzzy name match
        matches = client.find_project_by_name(name_or_id)
        if not matches:
            if as_json:
                # Return all projects so caller can choose
                projects = client.list_projects()
                output_json(
                    {
                        "error": f"未找到项目: {name_or_id}",
                        "code": "NOT_FOUND",
                        "available_projects": [p.to_json_dict() for p in projects],
                    }
                )
            else:
                output_error(f"未找到项目: {name_or_id}")
                console.print("\n[dim]可用项目:[/dim]")
                projects = client.list_projects()
                for p in projects:
                    console.print(f"  - {p.name} ({p.id})")
            raise typer.Exit(code=1)

        if len(matches) == 1:
            project_data = client.get_project_data(matches[0].id)
            display_project_data(project_data, as_json=as_json)
        else:
            if as_json:
                output_json(
                    {
                        "error": "多个项目匹配",
                        "code": "AMBIGUOUS",
                        "matches": [p.to_json_dict() for p in matches],
                    }
                )
                raise typer.Exit(code=1)
            else:
                console.print(f"[yellow]找到 {len(matches)} 个匹配项目:[/yellow]")
                for i, p in enumerate(matches, 1):
                    console.print(f"  {i}. {p.name} ({p.id})")
                choice = Prompt.ask("请选择项目编号", default="1")
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    project_data = client.get_project_data(matches[idx].id)
                    display_project_data(project_data, as_json=as_json)
                else:
                    output_error("无效的选择")
                    raise typer.Exit(code=1)
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


# ── Helper functions ─────────────────────────────────────────────────


def _resolve_project_id(client: DidaClient, name_or_id: str) -> str | None:
    """Resolve a project name or ID to a project ID."""
    # Try as ID first by checking project list
    projects = client.list_projects()
    for p in projects:
        if p.id == name_or_id:
            return p.id

    # Fuzzy name match
    name_lower = name_or_id.lower()
    matches = [p for p in projects if name_lower in p.name.lower()]
    if len(matches) == 1:
        return matches[0].id
    if len(matches) > 1:
        # Return first exact match if available
        exact = [p for p in matches if p.name.lower() == name_lower]
        if exact:
            return exact[0].id
        return matches[0].id
    return None


def _parse_date(date_str: str) -> str:
    """Parse a date string into ISO 8601 format for Dida365 API.

    Supports: "tomorrow", "today", ISO dates, date-only strings.
    """
    now = datetime.now(tz=timezone(timedelta(hours=8)))  # Asia/Shanghai

    if date_str.lower() == "today":
        dt = now.replace(hour=23, minute=59, second=0, microsecond=0)
    elif date_str.lower() == "tomorrow":
        dt = (now + timedelta(days=1)).replace(hour=23, minute=59, second=0, microsecond=0)
    else:
        try:
            # Try ISO format with time: 2026-03-01T15:00
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
        except ValueError:
            try:
                # Try date-only: 2026-03-01
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dt = dt.replace(hour=23, minute=59, second=0, tzinfo=timezone(timedelta(hours=8)))
            except ValueError:
                msg = (
                    f"无法解析日期: {date_str}. "
                    "支持格式: today, tomorrow, 2026-03-01, 2026-03-01T15:00"
                )
                raise ValueError(msg) from None

    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
