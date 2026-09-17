import dataclasses
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import Annotated
from typing import Final

import typer
from clockify import ProjectId
from clockify import TagId
from clockify import TaskId

from clockify_unofficial_cli.output.columns import TIME_ENTRIES
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.output.renderer import to_record
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.resolve import resolve_project
from clockify_unofficial_cli.services.resolve import resolve_tag
from clockify_unofficial_cli.services.resolve import resolve_task
from clockify_unofficial_cli.services.timer import LogRequest
from clockify_unofficial_cli.services.timer import TimerRequest
from clockify_unofficial_cli.services.timer import log_entry
from clockify_unofficial_cli.services.timer import parse_optional_duration
from clockify_unofficial_cli.services.timer import parse_optional_instant
from clockify_unofficial_cli.services.timer import running_entry
from clockify_unofficial_cli.services.timer import start_timer
from clockify_unofficial_cli.services.timer import stop_timer

APP: Final = typer.Typer(help="Timer shortcuts (start/stop/status/log).", no_args_is_help=True)


@dataclass(frozen=True, slots=True)
class _StartArgs:  # pylint: disable=too-many-instance-attributes
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: tuple[TagId, ...]
    billable: bool
    start: datetime | None


@dataclass(frozen=True, slots=True)
class _LogArgs:  # pylint: disable=too-many-instance-attributes
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: tuple[TagId, ...]
    billable: bool
    start: datetime | None
    end: datetime | None
    duration: timedelta | None


@APP.command(name="start", help="Start a new running timer; defaults to `now` when --from is omitted.")
@handle_errors
def start_cmd(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    description: Annotated[str | None, typer.Argument(help="Entry description.")] = None,
    *,
    project: Annotated[str | None, typer.Option("--project", "-P", help="Project ID or exact name.")] = None,
    task: Annotated[
        str | None, typer.Option("--task", "-t", help="Task ID or exact name; requires --project.")
    ] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Tag ID or exact name; pass multiple times.")] = None,
    billable: Annotated[bool, typer.Option("--billable/--no-billable", help="Mark the entry as billable.")] = False,
    from_: Annotated[str | None, typer.Option("--from", help="Start instant; defaults to now.")] = None,
) -> None:
    if task and not project:
        message = "--task requires --project because tasks are scoped to projects."
        raise CliError(message, exit_code=ExitCode.USAGE)
    app_context = get_app_context(ctx)
    project_id = ProjectId(resolve_project(app_context, project)) if project else None
    task_id = TaskId(resolve_task(app_context, project_id, task)) if task and project_id else None
    tag_ids = tuple(TagId(resolve_tag(app_context, term)) for term in (tag or ()))
    args = _StartArgs(
        description=description,
        project_id=project_id,
        task_id=task_id,
        tag_ids=tag_ids,
        billable=billable,
        start=parse_optional_instant(from_),
    )
    request = TimerRequest(
        description=args.description,
        project_id=args.project_id,
        task_id=args.task_id,
        tag_ids=args.tag_ids,
        billable=args.billable,
        start=args.start,
        end=None,
        duration=None,
    )
    entry = start_timer(app_context, request)
    app_context.render(single(_entry_as_record(entry), TIME_ENTRIES))


@APP.command(name="stop", help="Stop the currently running timer.")
@handle_errors
def stop_cmd(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    entry = stop_timer(app_context, end=None)
    app_context.render(single(_entry_as_record(entry), TIME_ENTRIES))


@APP.command(
    name="status", help="Show the currently running timer; exits OK with a stderr notice when none is active."
)
@handle_errors
def status_cmd(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    entry = running_entry(app_context)
    if entry is None:
        app_context.notify("No timer running.")
        raise typer.Exit(ExitCode.OK)
    app_context.render(single(_entry_as_record(entry), TIME_ENTRIES))


@APP.command(name="log", help="Log a finished entry; --duration with one of --from/--to, or both --from and --to.")
@handle_errors
def log_cmd(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    *,
    description: Annotated[str | None, typer.Option("--description", help="Entry description.")] = None,
    project: Annotated[str | None, typer.Option("--project", "-P", help="Project ID or exact name.")] = None,
    task: Annotated[
        str | None, typer.Option("--task", "-t", help="Task ID or exact name; requires --project.")
    ] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Tag ID or exact name; pass multiple times.")] = None,
    billable: Annotated[bool, typer.Option("--billable/--no-billable", help="Mark the entry as billable.")] = False,
    from_: Annotated[str | None, typer.Option("--from", help="Start instant.")] = None,
    to: Annotated[str | None, typer.Option("--to", help="End instant.")] = None,
    duration: Annotated[str | None, typer.Option("--duration", help="Duration, e.g. 1h30m.")] = None,
) -> None:
    if task and not project:
        message = "--task requires --project because tasks are scoped to projects."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if from_ is None and to is None and duration is None:
        message = "`log` needs --from/--to or --duration."
        raise CliError(message, exit_code=ExitCode.USAGE)
    app_context = get_app_context(ctx)
    project_id = ProjectId(resolve_project(app_context, project)) if project else None
    task_id = TaskId(resolve_task(app_context, project_id, task)) if task and project_id else None
    tag_ids = tuple(TagId(resolve_tag(app_context, term)) for term in (tag or ()))
    args = _LogArgs(
        description=description,
        project_id=project_id,
        task_id=task_id,
        tag_ids=tag_ids,
        billable=billable,
        start=parse_optional_instant(from_),
        end=parse_optional_instant(to),
        duration=parse_optional_duration(duration),
    )
    request = LogRequest(
        description=args.description,
        project_id=args.project_id,
        task_id=args.task_id,
        tag_ids=args.tag_ids,
        billable=args.billable,
        start=args.start,
        end=args.end,
        duration=args.duration,
    )
    entry = log_entry(app_context, request=request)
    app_context.render(single(_entry_as_record(entry), TIME_ENTRIES))


# Listed here so main.create_app can register each one as a root-level Typer command,
# matching the documented "start/stop/status/log" root shortcuts.
ROOT_COMMANDS: Final = (start_cmd, stop_cmd, status_cmd, log_cmd)


# Wrap the SDK time-entry object into a dict mapping so the renderer's to_record
# coercion accepts it without mypy complaining about `object` not being a BaseModel.
def _entry_as_record(entry: object) -> dict[str, object]:
    return dict(to_record(entry))


del dataclasses
