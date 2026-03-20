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
from dida.models import ChecklistItem, Project, Task, TaskPriority
from dida.output import (
    display_project,
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
    help="滴答清单 (Dida365) CLI 工具 — 管理任务和项目",
    no_args_is_help=True,
)

auth_app = typer.Typer(help="认证管理", no_args_is_help=True)
task_app = typer.Typer(
    help="任务管理 (create/get/update/complete/delete/move/filter/completed)", no_args_is_help=True
)
project_app = typer.Typer(
    help="项目管理 (create/list/get/update/delete)", no_args_is_help=True
)

app.add_typer(auth_app, name="auth")
app.add_typer(task_app, name="task")
app.add_typer(project_app, name="project")

console = Console()

# Common options
JsonOption = Annotated[bool, typer.Option("--json", help="输出 JSON 格式")]


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from dida import __version__

        print(f"dida {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version", "-V", help="显示版本号",
            callback=_version_callback, is_eager=True,
        ),
    ] = None,
) -> None:
    """滴答清单 (Dida365) CLI 工具。"""


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
    """检查环境并引导完成初始化配置。"""
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

    # JSON mode: report only, no interactive flow
    if as_json:
        output_json({"ok": all_ok, "checks": checks})
        if not all_ok:
            raise typer.Exit(code=1)
        return

    # Rich output — environment checks
    console.print("[bold]环境检查[/bold]")
    for check in checks:
        status = "[green]✓[/green]" if check["ok"] else "[red]✗[/red]"
        version = f" ({check['version']})" if "version" in check else ""
        console.print(f"  {status} {check['name']}{version}")

    console.print()

    if not py_ok:
        output_error("需要 Python 3.12+")
        raise typer.Exit(code=1)
    if not uv_ok:
        output_error("未找到 uv，请安装: https://docs.astral.sh/uv/")
        raise typer.Exit(code=1)

    # Interactive auth setup
    if not auth_ok:
        console.print("[bold]认证配置[/bold]")
        console.print("  需要滴答清单开发者应用的 Client ID 和 Client Secret。")
        console.print("  如果还没有，请前往 https://developer.dida365.com/ 注册应用，")
        console.print("  并设置回调地址为 [cyan]http://localhost:18365/callback[/cyan]")
        console.print()

        if Confirm.ask("是否现在进行认证?"):
            client_id = Prompt.ask("请输入 Client ID")
            client_secret = Prompt.ask("请输入 Client Secret")

            if not client_id or not client_secret:
                output_error("Client ID 和 Client Secret 不能为空")
                raise typer.Exit(code=1)

            console.print("[dim]正在打开浏览器进行授权...[/dim]")
            try:
                oauth_login(client_id, client_secret)
                output_success("认证成功！环境已就绪。")
            except RuntimeError as e:
                output_error(str(e))
                raise typer.Exit(code=1) from None
        else:
            console.print("[dim]跳过认证。稍后可运行 dida auth login 完成。[/dim]")
            raise typer.Exit(code=1)
    else:
        output_success("环境就绪")


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


@task_app.command("create")
def task_create(
    title: Annotated[str, typer.Argument(help="任务标题")],
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容/备注")] = None,
    desc: Annotated[str | None, typer.Option("--desc", help="Checklist 描述")] = None,
    tags: Annotated[str | None, typer.Option("--tags", help="标签 (逗号分隔)")] = None,
    all_day: Annotated[bool, typer.Option("--all-day", help="全天任务")] = False,
    start_date: Annotated[
        str | None,
        typer.Option(
            "--start-date", "-s",
            help="开始日期 (today/tomorrow/YYYY-MM-DD/ISO)",
        ),
    ] = None,
    due: Annotated[
        str | None,
        typer.Option("--due", "-d", help="截止日期 (today/tomorrow/YYYY-MM-DD/ISO)"),
    ] = None,
    timezone: Annotated[
        str | None, typer.Option("--timezone", help="时区 (默认 Asia/Shanghai)")
    ] = None,
    reminders: Annotated[
        str | None, typer.Option("--reminders", help="提醒 (逗号分隔 TRIGGER, 如 TRIGGER:PT0S)")
    ] = None,
    repeat: Annotated[
        str | None,
        typer.Option(
            "--repeat",
            help="重复规则 (RRULE, 如 RRULE:FREQ=DAILY;INTERVAL=1)",
        ),
    ] = None,
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    sort_order: Annotated[int | None, typer.Option("--sort-order", help="排序值")] = None,
    items: Annotated[
        str | None, typer.Option("--items", help='子任务 (JSON, 如 [{"title":"子任务1"}])')
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """创建新任务。支持所有 Dida365 API 参数。"""
    client = _get_client()
    try:
        task = Task(title=title)

        if priority:
            task.priority = TaskPriority.from_str(priority).value
        if due:
            task.due_date = _parse_date(due)
        if start_date:
            task.start_date = _parse_date(start_date)
        if project:
            pid = _resolve_project_id(client, project)
            if pid:
                task.project_id = pid
        if content:
            task.content = content
        if desc:
            task.desc = desc
        if tags:
            task.tags = [t.strip() for t in tags.split(",")]
        if all_day:
            task.all_day = True
        if timezone:
            task.time_zone = timezone
        if reminders:
            task.reminders = [r.strip() for r in reminders.split(",")]
        if repeat:
            task.repeat_flag = repeat
        if sort_order is not None:
            task.sort_order = sort_order
        if items:
            task.items = [ChecklistItem.from_dict(i) for i in json.loads(items)]

        created = client.create_task(task)
        display_task(created, as_json=as_json, action="已创建")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    except (ValueError, json.JSONDecodeError) as e:
        if as_json:
            output_error_json(str(e), "VALIDATION_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=1) from None
    finally:
        client.close()


# Deprecated alias: task add → task create
@task_app.command("add", hidden=True, deprecated=True)
def task_add(
    title: Annotated[str, typer.Argument(help="任务标题")],
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容/备注")] = None,
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    due: Annotated[
        str | None, typer.Option("--due", "-d", help="截止日期"),
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """[已弃用] 请使用 task create。"""
    task_create(
        title=title, project=project, content=content, priority=priority, due=due, as_json=as_json,
    )


@task_app.command("get")
def task_get(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """查看单个任务详情。"""
    client = _get_client()
    try:
        pid = project_id or client.find_task_project_id(task_id)
        if pid is None:
            if as_json:
                output_error_json(f"未找到任务: {task_id}", "NOT_FOUND")
            else:
                output_error(f"未找到任务: {task_id}")
            raise typer.Exit(code=1)

        task = client.get_task(pid, task_id)
        display_task(task, as_json=as_json, action="任务详情")
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
    content: Annotated[str | None, typer.Option("--content", "-c", help="任务内容")] = None,
    desc: Annotated[str | None, typer.Option("--desc", help="描述")] = None,
    tags: Annotated[str | None, typer.Option("--tags", help="标签 (逗号分隔)")] = None,
    all_day: Annotated[bool | None, typer.Option("--all-day/--no-all-day", help="全天任务")] = None,
    start_date: Annotated[
        str | None, typer.Option("--start-date", "-s", help="开始日期")
    ] = None,
    due: Annotated[str | None, typer.Option("--due", "-d", help="截止日期")] = None,
    timezone: Annotated[str | None, typer.Option("--timezone", help="时区")] = None,
    reminders: Annotated[str | None, typer.Option("--reminders", help="提醒 (逗号分隔)")] = None,
    repeat: Annotated[str | None, typer.Option("--repeat", help="重复规则 (RRULE)")] = None,
    priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="优先级: none/low/medium/high")
    ] = None,
    sort_order: Annotated[int | None, typer.Option("--sort-order", help="排序值")] = None,
    items: Annotated[
        str | None, typer.Option("--items", help='子任务 (JSON)')
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """更新任务。支持所有 Dida365 API 参数。"""
    client = _get_client()
    try:
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
        if content:
            task.content = content
        if desc:
            task.desc = desc
        if tags:
            task.tags = [t.strip() for t in tags.split(",")]
        if all_day is not None:
            task.all_day = all_day
        if start_date:
            task.start_date = _parse_date(start_date)
        if due:
            task.due_date = _parse_date(due)
        if timezone:
            task.time_zone = timezone
        if reminders:
            task.reminders = [r.strip() for r in reminders.split(",")]
        if repeat:
            task.repeat_flag = repeat
        if priority:
            task.priority = TaskPriority.from_str(priority).value
        if sort_order is not None:
            task.sort_order = sort_order
        if items:
            task.items = [ChecklistItem.from_dict(i) for i in json.loads(items)]

        updated = client.update_task(task)
        display_task(updated, as_json=as_json, action="已更新")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    except (ValueError, json.JSONDecodeError) as e:
        if as_json:
            output_error_json(str(e), "VALIDATION_ERROR")
        else:
            output_error(str(e))
        raise typer.Exit(code=1) from None
    finally:
        client.close()


@task_app.command("complete")
def task_complete(
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


# Deprecated alias: task done → task complete
@task_app.command("done", hidden=True, deprecated=True)
def task_done(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="项目 ID (跳过自动查找)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """[已弃用] 请使用 task complete。"""
    task_complete(task_id=task_id, project_id=project_id, as_json=as_json)


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


@task_app.command("move")
def task_move(
    task_id: Annotated[str, typer.Argument(help="任务 ID")],
    to: Annotated[str | None, typer.Option("--to", "-T", help="目标项目名称或 ID")] = None,
    from_project: Annotated[
        str | None, typer.Option("--from", "-F", help="源项目名称或 ID")
    ] = None,
    project_id: Annotated[
        str | None, typer.Option("--project-id", help="源项目 ID (跳过自动查找)")
    ] = None,
    to_project_id: Annotated[
        str | None, typer.Option("--to-project-id", help="目标项目 ID (跳过模糊匹配)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """移动任务到另一个项目。"""
    client = _get_client()
    try:
        # Resolve destination
        dest_pid = to_project_id
        if not dest_pid:
            if not to:
                msg = "必须提供 --to 或 --to-project-id"
                if as_json:
                    output_error_json(msg, "VALIDATION_ERROR")
                else:
                    output_error(msg)
                raise typer.Exit(code=1)
            dest_pid = _resolve_project_id(client, to)
            if not dest_pid:
                msg = f"未找到目标项目: {to}"
                if as_json:
                    output_error_json(msg, "NOT_FOUND")
                else:
                    output_error(msg)
                raise typer.Exit(code=1)

        # Resolve source
        src_pid = project_id
        if not src_pid:
            if from_project:
                src_pid = _resolve_project_id(client, from_project)
            else:
                src_pid = client.find_task_project_id(task_id)
        if not src_pid:
            msg = f"未找到任务所在项目: {task_id}"
            if as_json:
                output_error_json(msg, "NOT_FOUND")
            else:
                output_error(msg)
            raise typer.Exit(code=1)

        result = client.move_task(task_id, src_pid, dest_pid)
        if as_json:
            output_json({"success": True, "data": result})
        else:
            output_success(f"已移动任务 {task_id} 到项目 {dest_pid}")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


def _parse_status_list(status_str: str) -> list[int]:
    """Parse comma-separated status names to API values."""
    mapping = {"normal": 0, "completed": 2}
    result = []
    for s in status_str.split(","):
        s = s.strip().lower()
        if s not in mapping:
            valid = ", ".join(mapping.keys())
            msg = f"Invalid status '{s}'. Valid values: {valid}"
            raise ValueError(msg)
        result.append(mapping[s])
    return result


def _parse_priority_list(priority_str: str) -> list[int]:
    """Parse comma-separated priority names to API values."""
    result = []
    for p in priority_str.split(","):
        result.append(TaskPriority.from_str(p.strip()).value)
    return result


@task_app.command("filter")
def task_filter(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    start_date: Annotated[
        str | None, typer.Option("--start-date", "-s", help="开始日期过滤")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option("--end-date", "-e", help="结束日期过滤")
    ] = None,
    priority: Annotated[
        str | None,
        typer.Option("--priority", "-p", help="优先级过滤 (逗号分隔: none/low/medium/high)"),
    ] = None,
    tag: Annotated[
        str | None, typer.Option("--tag", help="标签过滤 (逗号分隔, AND 逻辑)")
    ] = None,
    status: Annotated[
        str | None, typer.Option("--status", help="状态过滤 (逗号分隔: normal/completed)")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """过滤查询任务。支持按项目、日期、优先级、标签、状态过滤。"""
    client = _get_client()
    try:
        project_ids = None
        if project:
            pid = _resolve_project_id(client, project)
            if pid is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_ids = [pid]

        parsed_start = _parse_date(start_date) if start_date else None
        parsed_end = _parse_date(end_date) if end_date else None
        parsed_priority = _parse_priority_list(priority) if priority else None
        parsed_tags = [t.strip() for t in tag.split(",")] if tag else None
        parsed_status = _parse_status_list(status) if status else None

        tasks = client.filter_tasks(
            project_ids=project_ids,
            start_date=parsed_start,
            end_date=parsed_end,
            priority=parsed_priority,
            tags=parsed_tags,
            status=parsed_status,
        )
        display_tasks(tasks, as_json=as_json)
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


@task_app.command("completed")
def task_completed(
    project: Annotated[str | None, typer.Option("--project", "-P", help="项目名称或 ID")] = None,
    start_date: Annotated[
        str | None, typer.Option("--start-date", "-s", help="完成时间起始")
    ] = None,
    end_date: Annotated[
        str | None, typer.Option("--end-date", "-e", help="完成时间结束")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """查看已完成任务。按完成时间范围过滤。"""
    client = _get_client()
    try:
        project_ids = None
        if project:
            pid = _resolve_project_id(client, project)
            if pid is None:
                if as_json:
                    output_error_json(f"未找到项目: {project}", "NOT_FOUND")
                else:
                    output_error(f"未找到项目: {project}")
                raise typer.Exit(code=1)
            project_ids = [pid]

        parsed_start = _parse_date(start_date) if start_date else None
        parsed_end = _parse_date(end_date) if end_date else None

        tasks = client.list_completed_tasks(
            project_ids=project_ids,
            start_date=parsed_start,
            end_date=parsed_end,
        )
        display_tasks(tasks, as_json=as_json)
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


# ── Project commands ─────────────────────────────────────────────────


@project_app.command("create")
def project_create(
    name: Annotated[str, typer.Argument(help="项目名称")],
    color: Annotated[str | None, typer.Option("--color", help="颜色 (如 #F18181)")] = None,
    view_mode: Annotated[
        str | None, typer.Option("--view-mode", help="视图模式: list/kanban/timeline")
    ] = None,
    kind: Annotated[
        str | None, typer.Option("--kind", help="类型: TASK/NOTE")
    ] = None,
    sort_order: Annotated[int | None, typer.Option("--sort-order", help="排序值")] = None,
    as_json: JsonOption = False,
) -> None:
    """创建新项目。"""
    client = _get_client()
    try:
        proj = Project(name=name)
        if color:
            proj.color = color
        if view_mode:
            proj.view_mode = view_mode
        if kind:
            proj.kind = kind
        if sort_order is not None:
            proj.sort_order = sort_order

        created = client.create_project(proj)
        display_project(created, as_json=as_json, action="已创建")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


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


@project_app.command("get")
def project_get(
    name_or_id: Annotated[str, typer.Argument(help="项目名称或 ID")],
    as_json: JsonOption = False,
) -> None:
    """查看项目详情及任务。"""
    client = _get_client()
    try:
        # Try as ID first
        try:
            project_data = client.get_project_data(name_or_id)
            if project_data.project.id:
                display_project_data(project_data, as_json=as_json)
                return
        except ApiError:
            pass

        # Try fuzzy name match
        matches = client.find_project_by_name(name_or_id)
        if not matches:
            if as_json:
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


# Deprecated alias: project show → project get
@project_app.command("show", hidden=True, deprecated=True)
def project_show(
    name_or_id: Annotated[str, typer.Argument(help="项目名称或 ID")],
    as_json: JsonOption = False,
) -> None:
    """[已弃用] 请使用 project get。"""
    project_get(name_or_id=name_or_id, as_json=as_json)


@project_app.command("update")
def project_update(
    project_id: Annotated[str, typer.Argument(help="项目 ID")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="新名称")] = None,
    color: Annotated[str | None, typer.Option("--color", help="颜色")] = None,
    view_mode: Annotated[
        str | None, typer.Option("--view-mode", help="视图模式: list/kanban/timeline")
    ] = None,
    kind: Annotated[str | None, typer.Option("--kind", help="类型: TASK/NOTE")] = None,
    sort_order: Annotated[int | None, typer.Option("--sort-order", help="排序值")] = None,
    as_json: JsonOption = False,
) -> None:
    """更新项目。"""
    client = _get_client()
    try:
        proj = Project()
        if name:
            proj.name = name
        if color:
            proj.color = color
        if view_mode:
            proj.view_mode = view_mode
        if kind:
            proj.kind = kind
        if sort_order is not None:
            proj.sort_order = sort_order

        updated = client.update_project(project_id, proj)
        display_project(updated, as_json=as_json, action="已更新")
    except (ApiError, AuthError) as e:
        _handle_error(e, as_json=as_json)
    finally:
        client.close()


@project_app.command("delete")
def project_delete(
    project_id: Annotated[str, typer.Argument(help="项目 ID")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="跳过确认")] = False,
    as_json: JsonOption = False,
) -> None:
    """删除项目。"""
    client = _get_client()
    try:
        if not as_json and not yes and not Confirm.ask(f"确认删除项目 {project_id}?"):
            console.print("[dim]已取消[/dim]")
            raise typer.Exit(code=0)

        client.delete_project(project_id)
        if as_json:
            output_json({"success": True, "data": {"id": project_id, "status": "deleted"}})
        else:
            output_success(f"已删除项目: {project_id}")
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
