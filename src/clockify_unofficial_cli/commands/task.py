import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ProjectId
from clockify import TaskCreate
from clockify import TaskStatus
from clockify import TaskUpdate
from clockify import UserId

from clockify_unofficial_cli.output.columns import TASKS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_project
from clockify_unofficial_cli.services.resolve import resolve_task

APP: Final = typer.Typer(help="Manage tasks inside a project.", no_args_is_help=True)


def _project_id(app_context: object, term: str) -> ProjectId:
    resolved = resolve_project(app_context, term)  # type: ignore[arg-type]
    return ProjectId(resolved)


@dataclass(frozen=True, slots=True)
class _ListArgs:
    project: str
    limit: int | None
    page: int | None
    page_size: int | None


@APP.command(name="list", help="List tasks for the named project.")
@handle_errors
def list_tasks(
    ctx: typer.Context,
    *,
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")],
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N tasks; incompatible with --page/--page-size."),
    ] = None,
    page: Annotated[
        int | None,
        typer.Option("--page", help="1-based page number when paging through results."),
    ] = None,
    page_size: Annotated[
        int | None,
        typer.Option("--page-size", help="Page size when paging through results."),
    ] = None,
) -> None:
    args = _ListArgs(project=project, limit=limit, page=page, page_size=page_size)
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    project_id = _project_id(app_context, args.project)
    tasks = list_from_options(
        lambda: workspace.tasks.list(project_id),
        lambda **kwargs: workspace.tasks.list_page(project_id, **kwargs),
        args.limit,
        args.page,
        args.page_size,
    )
    app_context.render(many(tasks, TASKS))


@dataclass(frozen=True, slots=True)
class _TaskProjectArgs:
    project: str


@APP.command(help="Show a task by ID or name within the named project.")
@handle_errors
def get(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Task ID or exact name.")],
    *,
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")],
) -> None:
    args = _TaskProjectArgs(project=project)
    app_context = get_app_context(ctx)
    project_id = _project_id(app_context, args.project)
    task_id = resolve_task(app_context, project_id, term)
    task = app_context.workspace().tasks.get(project_id, task_id)
    app_context.render(single(task, TASKS))


@dataclass(frozen=True, slots=True)
class _CreateArgs:
    project: str
    name: str
    assignee_ids: list[UserId] | None
    estimate: str | None
    status: TaskStatus | None


@APP.command(help="Create a new task under the named project.")
@handle_errors
def create(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")],
    name: Annotated[str, typer.Option("--name", help="Task display name.")],
    assignee: Annotated[
        str | None,
        typer.Option("--assignee", help="Assignee user ID."),
    ] = None,
    estimate: Annotated[
        str | None,
        typer.Option("--estimate", help="ISO-8601 duration estimate, e.g. PT2H30M."),
    ] = None,
    status: Annotated[
        TaskStatus | None,
        typer.Option("--status", case_sensitive=False, help="ACTIVE or DONE."),
    ] = None,
) -> None:
    args = _CreateArgs(
        project=project,
        name=name,
        assignee_ids=[UserId(assignee)] if assignee else None,
        estimate=estimate,
        status=status,
    )
    app_context = get_app_context(ctx)
    project_id = _project_id(app_context, args.project)
    payload = TaskCreate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None and k != "project"})
    task = app_context.workspace().tasks.create(project_id, payload)
    app_context.render(single(task, TASKS))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    project: str
    name: str | None
    assignee_ids: list[UserId] | None
    estimate: str | None
    status: TaskStatus | None


@APP.command(help="Update an existing task.")
@handle_errors
def update(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Task ID or exact name.")],
    *,
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")],
    name: Annotated[
        str | None,
        typer.Option("--name", help="New task display name."),
    ] = None,
    assignee: Annotated[
        str | None,
        typer.Option("--assignee", help="New assignee user ID."),
    ] = None,
    estimate: Annotated[
        str | None,
        typer.Option("--estimate", help="New ISO-8601 duration estimate."),
    ] = None,
    status: Annotated[
        TaskStatus | None,
        typer.Option("--status", case_sensitive=False, help="ACTIVE or DONE."),
    ] = None,
) -> None:
    args = _UpdateArgs(
        project=project,
        name=name,
        assignee_ids=[UserId(assignee)] if assignee else None,
        estimate=estimate,
        status=status,
    )
    app_context = get_app_context(ctx)
    project_id = _project_id(app_context, args.project)
    task_id = resolve_task(app_context, project_id, term)
    payload = TaskUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None and k != "project"})
    task = app_context.workspace().tasks.update(project_id, task_id, payload)
    app_context.render(single(task, TASKS))


@APP.command(help="Delete a task.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Task ID or exact name.")],
    *,
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete task '{term}'", assume_yes=yes)
    project_id = _project_id(app_context, project)
    task_id = resolve_task(app_context, project_id, term)
    app_context.workspace().tasks.delete(project_id, task_id)
    app_context.notify(f"Deleted task '{task_id}'.")
