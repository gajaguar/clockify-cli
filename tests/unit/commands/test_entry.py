from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    import typer
    from typer.testing import CliRunner

ENTRY_PAYLOAD: Final = {
    "id": "666666666666666666666666",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
    "userId": USER_PAYLOAD["id"],
    "description": "spike",
    "projectId": None,
    "taskId": None,
    "tagIds": None,
    "billable": False,
    "timeInterval": {
        "start": "2026-09-17T09:00:00Z",
        "end": "2026-09-17T10:00:00Z",
        "duration": "PT1H",
    },
    "customFieldValues": None,
    "type": "REGULAR",
    "isLocked": False,
}

TIME_ENTRIES_PATH: Final = (
    f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/user/{USER_PAYLOAD['id']}/time-entries"
)


@respx.mock
def test_entry_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(TIME_ENTRIES_PATH).mock(return_value=Response(200, json=[ENTRY_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "entry", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [ENTRY_PAYLOAD]


@respx.mock
def test_entry_get_by_id(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/time-entries/{ENTRY_PAYLOAD['id']}").mock(
        return_value=Response(200, json=ENTRY_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "entry", "get", ENTRY_PAYLOAD["id"]])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == ENTRY_PAYLOAD


@respx.mock
def test_entry_create_requires_from_and_to(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["entry", "create"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_entry_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.delete(
        f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/time-entries/{ENTRY_PAYLOAD['id']}"
    ).mock(return_value=Response(204))
    # Act
    result = runner.invoke(cli, ["entry", "delete", ENTRY_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_start_shortcut_sends_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(TIME_ENTRIES_PATH).mock(return_value=Response(201, json=ENTRY_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "start", "spike"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_stop_shortcut_sends_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.patch(TIME_ENTRIES_PATH).mock(return_value=Response(200, json=ENTRY_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "stop"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_status_shortcut_returns_ok_when_empty(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(TIME_ENTRIES_PATH).mock(return_value=Response(200, json=[]))
    # Act
    result = runner.invoke(cli, ["status"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "No timer running." in result.output


@respx.mock
def test_log_shortcut_sends_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/time-entries").mock(
        return_value=Response(201, json=ENTRY_PAYLOAD)
    )
    # Act
    result = runner.invoke(
        cli,
        ["-o", "json", "log", "--from", "2026-09-17T09:00", "--to", "2026-09-17T10:00", "--description", "spike"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
