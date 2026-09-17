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

USER_A: Final = {
    "id": "5b0f5b1f1f1f1f1f1f1f1faa",
    "email": "alpha@example.com",
    "name": "Alpha User",
    "activeWorkspace": USER_PAYLOAD["activeWorkspace"],
    "defaultWorkspace": USER_PAYLOAD["defaultWorkspace"],
    "status": "ACTIVE",
}
USER_B: Final = {
    "id": "5b0f5b1f1f1f1f1f1f1f1fbb",
    "email": "beta@example.com",
    "name": "Beta User",
    "activeWorkspace": USER_PAYLOAD["activeWorkspace"],
    "defaultWorkspace": USER_PAYLOAD["defaultWorkspace"],
    "status": "ACTIVE",
}


@respx.mock
def test_user_me_renders_authenticated_user(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "user", "me"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == USER_PAYLOAD


@respx.mock
def test_user_list_renders_workspace_members(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/users").mock(
        return_value=Response(200, json=[USER_A, USER_B])
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "user", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [USER_A, USER_B]


@respx.mock
def test_user_list_honours_limit(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/users").mock(
        return_value=Response(200, json=[USER_A, USER_B])
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "user", "list", "--limit", "1"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [USER_A]
