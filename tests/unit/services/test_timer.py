from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.timer import LogRequest
from clockify_unofficial_cli.services.timer import TimerRequest
from clockify_unofficial_cli.services.timer import log_entry
from clockify_unofficial_cli.services.timer import running_entry
from clockify_unofficial_cli.services.timer import start_timer
from clockify_unofficial_cli.services.timer import stop_timer


class _FakeEntries:
    def __init__(self, entries: list[object]) -> None:
        self._entries = entries
        self.sent: list[tuple[object, dict[str, object] | None]] = []

    def list(self, user_id: object, entry_filter: object | None = None) -> list[object]:
        self.sent.append((user_id, None))
        if entry_filter is not None and getattr(entry_filter, "in_progress", False):
            return [e for e in self._entries if getattr(e, "running", False)]
        return self._entries

    def start(self, user_id: object, payload: object) -> object:
        self.sent.append((user_id, {"start": payload}))
        return MagicMock()

    def stop(self, user_id: object, end: datetime.datetime | None = None) -> object:
        self.sent.append((user_id, {"stop": end}))
        return MagicMock()

    def create(self, payload: object) -> object:
        self.sent.append(("create", {"payload": payload}))
        return MagicMock()


class _FakeWorkspace:
    def __init__(self, entries: list[object]) -> None:
        self.time_entries = _FakeEntries(entries)


def _app_context(entries: list[object]) -> AppContext:
    workspace = _FakeWorkspace(entries)
    context = MagicMock(spec=AppContext)
    context.workspace.return_value = workspace
    context.user_id.return_value = "user-1"
    return context


def test_start_timer_sends_payload() -> None:
    # Arrange
    context = _app_context([])
    start = datetime.datetime(2026, 9, 17, 9, 0, tzinfo=datetime.UTC)
    request = TimerRequest(
        description="spike",
        project_id=None,
        task_id=None,
        tag_ids=(),
        billable=False,
        start=start,
        end=None,
        duration=None,
    )
    # Act
    start_timer(context, request)
    # Assert
    sent = context.workspace().time_entries.sent
    payload = sent[0][1]["start"]
    assert sent == [
        (
            "user-1",
            {
                "start": payload.__class__(
                    start=start,
                    end=None,
                    billable=None,
                    description="spike",
                    project_id=None,
                    task_id=None,
                    tag_ids=None,
                )
            },
        )
    ]


def test_start_timer_defaults_start_to_now() -> None:
    # Arrange
    context = _app_context([])
    request = TimerRequest(
        description="now",
        project_id=None,
        task_id=None,
        tag_ids=(),
        billable=False,
        start=None,
        end=None,
        duration=None,
    )
    # Act
    start_timer(context, request)
    # Assert
    sent = context.workspace().time_entries.sent
    expected_payload = sent[0][1]["start"]
    assert sent == [("user-1", {"start": expected_payload})]
    assert expected_payload.description == "now"
    assert expected_payload.start.tzinfo == datetime.UTC


def test_stop_timer_passes_end() -> None:
    # Arrange
    context = _app_context([])
    end = datetime.datetime(2026, 9, 17, 10, 0, tzinfo=datetime.UTC)
    # Act
    stop_timer(context, end=end)
    # Assert
    sent = context.workspace().time_entries.sent
    assert sent == [("user-1", {"stop": end})]


def test_running_entry_returns_first_in_progress_entry() -> None:
    # Arrange
    pending_entry = MagicMock(running=False)
    running_entry_mock = MagicMock(running=True)
    entries = [pending_entry, running_entry_mock]
    context = _app_context(entries)
    # Act
    result = running_entry(context)
    # Assert
    assert result is running_entry_mock


def test_running_entry_returns_none_when_empty() -> None:
    # Arrange
    context = _app_context([])
    # Act
    result = running_entry(context)
    # Assert
    assert result is None


def test_log_entry_with_start_and_end() -> None:
    # Arrange
    context = _app_context([])
    start = datetime.datetime(2026, 9, 17, 9, 0, tzinfo=datetime.UTC)
    end = datetime.datetime(2026, 9, 17, 10, 0, tzinfo=datetime.UTC)
    request = LogRequest(
        description="log",
        project_id=None,
        task_id=None,
        tag_ids=(),
        billable=False,
        start=start,
        end=end,
        duration=None,
    )
    # Act
    log_entry(context, request=request)
    # Assert
    sent = context.workspace().time_entries.sent
    payload = sent[0][1]["payload"]
    assert payload.start == start
    assert payload.end == end


def test_log_entry_with_only_duration_complains() -> None:
    # Arrange
    context = _app_context([])
    request = LogRequest(
        description="log",
        project_id=None,
        task_id=None,
        tag_ids=(),
        billable=False,
        start=None,
        end=None,
        duration=None,
    )
    # Act
    with pytest.raises(CliError) as caught:
        log_entry(context, request=request)
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
