from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    import typer
    from typer.testing import CliRunner

    from clockify_unofficial_cli.runtime.context import Services

WORKSPACE_A: Final = {
    "id": "64a1f0000000000000000001",
    "name": "Workspace Alpha",
    "imageUrl": "",
    "hourlyRate": {"amount": 0, "currency": None},
    "costRate": None,
}
WORKSPACE_B: Final = {
    "id": "64a1f0000000000000000002",
    "name": "Workspace Beta",
    "imageUrl": "",
    "hourlyRate": {"amount": 0, "currency": None},
    "costRate": None,
}


@respx.mock
def test_workspace_list_renders_two_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=Response(200, json=[WORKSPACE_A, WORKSPACE_B]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "workspace", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    payload = json.loads(result.stdout)
    assert {item["id"]: item["name"] for item in payload} == {
        WORKSPACE_A["id"]: WORKSPACE_A["name"],
        WORKSPACE_B["id"]: WORKSPACE_B["name"],
    }


@respx.mock
def test_workspace_get_by_id(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=Response(200, json=[WORKSPACE_A, WORKSPACE_B]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "workspace", "get", WORKSPACE_A["id"]])
    # Assert
    assert result.exit_code == ExitCode.OK
    payload = json.loads(result.stdout)
    expected = {"id": WORKSPACE_A["id"], "name": WORKSPACE_A["name"]}
    assert {key: payload[key] for key in expected} == expected


@respx.mock
def test_workspace_use_persists_workspace_id(
    runner: CliRunner, cli: typer.Typer, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=Response(200, json=[WORKSPACE_A, WORKSPACE_B]))
    services.settings.save(Settings(profiles={"default": Profile()}))
    # Act
    result = runner.invoke(cli, ["workspace", "use", WORKSPACE_B["name"]])
    # Assert
    assert result.exit_code == ExitCode.OK
    settings = services.settings.load()
    expected = Settings(profiles={"default": Profile(workspace_id=WORKSPACE_B["id"])})
    assert settings == expected


@respx.mock
def test_workspace_use_with_unknown_workspace_exits_not_found(
    runner: CliRunner, cli: typer.Typer, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=Response(200, json=[WORKSPACE_A, WORKSPACE_B]))
    services.settings.save(Settings(profiles={"default": Profile()}))
    # Act
    result = runner.invoke(cli, ["workspace", "use", "no-such-workspace"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_workspace_use_without_profile_exits_configuration(
    runner: CliRunner, cli: typer.Typer, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/workspaces").mock(return_value=Response(200, json=[WORKSPACE_A, WORKSPACE_B]))
    services.settings.save(Settings())
    # Act
    result = runner.invoke(cli, ["workspace", "use", WORKSPACE_A["name"]])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
