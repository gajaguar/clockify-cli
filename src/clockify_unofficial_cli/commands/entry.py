import dataclasses
import datetime
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ProjectId
from clockify import TagId
from clockify import TaskId
from clockify import TimeEntryCreate
from clockify import TimeEntryFilter
from clockify import TimeEntryUpdate

from clockify_unofficial_cli.output.columns import TIME_ENTRIES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_project
from clockify_unofficial_cli.services.resolve import resolve_tag
from clockify_unofficial_cli.services.resolve import resolve_task

APP: Final = typer.Typer(help="Manage time entries.", no_args_is_help=True)


def _optional_project_id(app_context: AppContext, term: str | None) -> ProjectId | None:
    return ProjectId(resolve_project(app_context, term)) if term else None


def _optional_task_id(app_context: AppContext, term: str | None, project_id: ProjectId | None) -> TaskId | None:
    if not term or project_id is None:
        return None
    return TaskId(resolve_task(app_context, project_id, term))


def _optional_tag_ids(app_context: AppContext, terms: tuple[str, ...] | None) -> list[TagId] | None:
    if not terms:
        return None
    return [TagId(resolve_tag(app_context, term)) for term in terms]


@dataclass(frozen=True, slots=True)
class _ListArgs:  # pylint: disable=too-many-instance-attributes
    description: str | None
    start: datetime.datetime | None
    end: datetime.datetime | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: list[TagId] | None
    limit: int | None
    page: int | None
    page_size: int | None


@APP.command(name="list", help="List time entries for the current user.")
@handle_errors
def list_entries(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    *,
    description: Annotated[
        str | None,
        typer.Option("--description", help="Substring filter on the entry description."),
    ] = None,
    from_: Annotated[
        datetime.datetime | None,
        typer.Option("--from", help="Lower bound on start, e.g. 2026-09-17T09:00 or 'yesterday 09:00'."),
    ] = None,
    to: Annotated[
        datetime.datetime | None,
        typer.Option("--to", help="Upper bound on start."),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", "-P", help="Filter by project ID or exact name."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", "-t", help="Filter by task ID or exact name; requires --project."),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Filter by tag ID or exact name; pass multiple times."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N entries; incompatible with --page/--page-size."),
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
    app_context = get_app_context(ctx)
    if task and not project:
        message = "--task requires --project because tasks are scoped to projects."
        raise CliError(message, exit_code=ExitCode.USAGE)
    workspace = app_context.workspace()
    project_id = _optional_project_id(app_context, project)
    args = _ListArgs(
        description=description,
        start=from_,
        end=to,
        project_id=project_id,
        task_id=_optional_task_id(app_context, task, project_id),
        tag_ids=_optional_tag_ids(app_context, tuple(tag) if tag else None),
        limit=limit,
        page=page,
        page_size=page_size,
    )
    entry_filter = TimeEntryFilter(
        description=args.description,
        start=args.start,
        end=args.end,
        project=args.project_id,
        task=args.task_id,
        tag_ids=args.tag_ids,
    )
    user_id = app_context.user_id()
    entries = list_from_options(
        lambda: workspace.time_entries.list(user_id, entry_filter=entry_filter),
        lambda **kwargs: workspace.time_entries.list_page(user_id, entry_filter=entry_filter, **kwargs),
        args.limit,
        args.page,
        args.page_size,
    )
    app_context.render(many(entries, TIME_ENTRIES))


@APP.command(help="Show a time entry by ID.")
@handle_errors
def get(
    ctx: typer.Context,
    entry_id: Annotated[str, typer.Argument(help="Time entry ID.")],
) -> None:
    app_context = get_app_context(ctx)
    entry = app_context.workspace().time_entries.get(entry_id)
    app_context.render(single(entry, TIME_ENTRIES))


@dataclass(frozen=True, slots=True)
class _CreateArgs:
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: list[TagId] | None
    billable: bool
    start: datetime.datetime | None
    end: datetime.datetime | None


@APP.command(help="Create a finished time entry (use `start` for a running entry).")
@handle_errors
def create(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    description: Annotated[
        str | None,
        typer.Option("--description", help="Entry description."),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", "-P", help="Project ID or exact name."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", "-t", help="Task ID or exact name; requires --project."),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Tag ID or exact name; pass multiple times."),
    ] = None,
    billable: Annotated[
        bool,
        typer.Option("--billable/--no-billable", help="Mark the entry as billable."),
    ] = False,
    from_: Annotated[
        datetime.datetime | None,
        typer.Option("--from", help="Start instant; e.g. 2026-09-17T09:00 or 'yesterday 09:00'."),
    ] = None,
    to: Annotated[
        datetime.datetime | None,
        typer.Option("--to", help="End instant."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    if from_ is None or to is None:
        message = "`entry create` requires both --from and --to; use `log` for open ranges."
        raise CliError(message, exit_code=ExitCode.USAGE)
    project_id = _optional_project_id(app_context, project)
    args = _CreateArgs(
        description=description,
        project_id=project_id,
        task_id=_optional_task_id(app_context, task, project_id),
        tag_ids=_optional_tag_ids(app_context, tuple(tag) if tag else None),
        billable=billable,
        start=from_,
        end=to,
    )
    payload = TimeEntryCreate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    entry = app_context.workspace().time_entries.create(payload)
    app_context.render(single(entry, TIME_ENTRIES))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: list[TagId] | None
    billable: bool | None
    start: datetime.datetime
    end: datetime.datetime | None


@APP.command(help="Update an existing time entry (start is required by the SDK).")
@handle_errors
def update(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    entry_id: Annotated[str, typer.Argument(help="Time entry ID.")],
    *,
    description: Annotated[
        str | None,
        typer.Option("--description", help="New description."),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", "-P", help="New project ID or exact name."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", "-t", help="New task ID or exact name; requires --project."),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", help="New tag IDs/names; pass multiple times."),
    ] = None,
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--no-billable", help="Toggle billable."),
    ] = None,
    from_: Annotated[
        datetime.datetime | None,
        typer.Option("--from", help="New start instant; required because Clockify PUT replaces the entry."),
    ] = None,
    to: Annotated[
        datetime.datetime | None,
        typer.Option("--to", help="New end instant."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    existing = workspace.time_entries.get(entry_id)
    project_id = _optional_project_id(app_context, project)
    if from_ is None:
        from_ = existing.time_interval.start
    args = _UpdateArgs(
        description=description,
        project_id=project_id,
        task_id=_optional_task_id(app_context, task, project_id),
        tag_ids=_optional_tag_ids(app_context, tuple(tag) if tag else None),
        billable=billable,
        start=from_,
        end=to,
    )
    payload = TimeEntryUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    entry = workspace.time_entries.update(entry_id, payload)
    app_context.render(single(entry, TIME_ENTRIES))


@APP.command(help="Delete a time entry.")
@handle_errors
def delete(
    ctx: typer.Context,
    entry_id: Annotated[str, typer.Argument(help="Time entry ID.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete time entry '{entry_id}'", assume_yes=yes)
    app_context.workspace().time_entries.delete(entry_id)
    app_context.notify(f"Deleted time entry '{entry_id}'.")
