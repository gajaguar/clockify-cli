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

CLIENT_PAYLOAD: Final = {
    "id": "aaaaaaaaaaaaaaaaaaaaaaaa",
    "name": "Acme Co.",
    "email": "billing@acme.test",
    "address": "1 Main St",
    "note": "VIP",
    "archived": False,
    "ccEmails": None,
    "currencyId": None,
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
}


def _client_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/clients"


@respx.mock
def test_client_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[CLIENT_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "client", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [CLIENT_PAYLOAD]


@respx.mock
def test_client_get_resolves_name(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[CLIENT_PAYLOAD]))
    respx.get(f"{_client_path(USER_PAYLOAD['activeWorkspace'])}/{CLIENT_PAYLOAD['id']}").mock(
        return_value=Response(200, json=CLIENT_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "client", "get", "Acme Co."])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == CLIENT_PAYLOAD


@respx.mock
def test_client_create_posts_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(201, json=CLIENT_PAYLOAD)
    )
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "client",
            "create",
            "--name",
            "Acme Co.",
            "--email",
            "billing@acme.test",
            "--address",
            "1 Main St",
            "--note",
            "VIP",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == CLIENT_PAYLOAD
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Acme Co.", "email": "billing@acme.test", "address": "1 Main St", "note": "VIP"}


@respx.mock
def test_client_update_omits_unchanged_fields(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[CLIENT_PAYLOAD]))
    route = respx.put(f"{_client_path(USER_PAYLOAD['activeWorkspace'])}/{CLIENT_PAYLOAD['id']}").mock(
        return_value=Response(200, json=CLIENT_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "client", "update", CLIENT_PAYLOAD["id"], "--name", "New Name"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "New Name"}


@respx.mock
def test_client_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[CLIENT_PAYLOAD]))
    route = respx.delete(f"{_client_path(USER_PAYLOAD['activeWorkspace'])}/{CLIENT_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["client", "delete", CLIENT_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_client_get_unknown_name_exits_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_client_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[CLIENT_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["client", "get", "Zzz"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND
