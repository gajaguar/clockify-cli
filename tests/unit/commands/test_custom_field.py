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

FIELD_PAYLOAD: Final = {
    "id": "444444444444444444444444",
    "name": "Priority",
    "type": "TXT",
    "entityType": "TIMEENTRY",
    "status": "VISIBLE",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
    "allowedValues": None,
    "workspaceDefaultValue": None,
    "placeholder": None,
    "description": None,
    "required": False,
    "onlyAdminCanEdit": False,
}


def _custom_field_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/custom-fields"


@respx.mock
def test_custom_field_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_custom_field_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(200, json=[FIELD_PAYLOAD])
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "custom-field", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [FIELD_PAYLOAD]


@respx.mock
def test_custom_field_create_requires_type(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(_custom_field_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(201, json=FIELD_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "custom-field", "create", "--name", "Priority", "--type", "TXT"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Priority", "type": "TXT"}


@respx.mock
def test_custom_field_update_omits_unchanged_fields(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_custom_field_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(200, json=[FIELD_PAYLOAD])
    )
    route = respx.put(f"{_custom_field_path(USER_PAYLOAD['activeWorkspace'])}/{FIELD_PAYLOAD['id']}").mock(
        return_value=Response(200, json=FIELD_PAYLOAD)
    )
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "custom-field",
            "update",
            "Priority",
            "--required",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"required": True}


@respx.mock
def test_custom_field_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_custom_field_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(200, json=[FIELD_PAYLOAD])
    )
    route = respx.delete(f"{_custom_field_path(USER_PAYLOAD['activeWorkspace'])}/{FIELD_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["custom-field", "delete", FIELD_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
