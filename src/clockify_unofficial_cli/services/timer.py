import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from clockify import TimeEntryCreate
from clockify import TimeEntryFilter

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.parsing import parse_duration
from clockify_unofficial_cli.services.parsing import parse_instant

if TYPE_CHECKING:
    from clockify import ProjectId
    from clockify import TagId
    from clockify import TaskId

    from clockify_unofficial_cli.runtime.context import AppContext


# Per-invocation bundle so the timer service can build a Clockify payload without
# growing a long positional argument list every time a new flag appears.
@dataclass(frozen=True, slots=True)
class TimerRequest:  # pylint: disable=too-many-instance-attributes,duplicate-code
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: tuple[TagId, ...]
    billable: bool
    start: datetime.datetime | None
    end: datetime.datetime | None
    duration: datetime.timedelta | None


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def start_timer(app_context: AppContext, request: TimerRequest) -> object:
    resolved_start = request.start if request.start is not None else _now()
    payload = TimeEntryCreate(
        start=resolved_start,
        end=request.end,
        billable=request.billable or None,
        description=request.description,
        project_id=request.project_id,
        task_id=request.task_id,
        tag_ids=list(request.tag_ids) if request.tag_ids else None,
    )
    return app_context.workspace().time_entries.start(app_context.user_id(), payload)


def stop_timer(app_context: AppContext, *, end: datetime.datetime | None) -> object:
    return app_context.workspace().time_entries.stop(app_context.user_id(), end=end)


def running_entry(app_context: AppContext) -> object | None:

    entries = list(
        app_context.workspace().time_entries.list(
            app_context.user_id(),
            entry_filter=TimeEntryFilter(in_progress=True),
        )
    )
    return entries[0] if entries else None


@dataclass(frozen=True, slots=True)
class LogRequest:  # pylint: disable=too-many-instance-attributes,duplicate-code
    description: str | None
    project_id: ProjectId | None
    task_id: TaskId | None
    tag_ids: tuple[TagId, ...]
    billable: bool
    start: datetime.datetime | None
    end: datetime.datetime | None
    duration: datetime.timedelta | None


def log_entry(
    app_context: AppContext,
    request: LogRequest,
) -> object:
    if request.start is not None and request.end is not None and request.duration is None:
        resolved_start, resolved_end = request.start, request.end
    elif request.start is not None and request.duration is not None and request.end is None:
        resolved_start, resolved_end = request.start, request.start + request.duration
    elif request.end is not None and request.duration is not None and request.start is None:
        resolved_start, resolved_end = request.end - request.duration, request.end
    elif request.duration is not None and request.start is None and request.end is None:
        resolved_start, resolved_end = _now() - request.duration, _now()
    else:
        message = "`log` needs --from/--to or --duration (exactly one pairing)."
        raise CliError(message, exit_code=ExitCode.USAGE)
    payload = TimeEntryCreate(
        start=resolved_start,
        end=resolved_end,
        billable=request.billable or None,
        description=request.description,
        project_id=request.project_id,
        task_id=request.task_id,
        tag_ids=list(request.tag_ids) if request.tag_ids else None,
    )
    return app_context.workspace().time_entries.create(payload)


def parse_optional_duration(value: str | None) -> datetime.timedelta | None:
    if value is None:
        return None
    return parse_duration(value)


def parse_optional_instant(value: str | None) -> datetime.datetime | None:
    if value is None:
        return None
    return parse_instant(value)


__all__ = [
    "TimerRequest",
    "log_entry",
    "parse_optional_duration",
    "parse_optional_instant",
    "running_entry",
    "start_timer",
    "stop_timer",
]
