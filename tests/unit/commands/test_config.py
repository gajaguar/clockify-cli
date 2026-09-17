from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

from clockify import Region

from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    import typer
    from typer.testing import CliRunner

    from clockify_unofficial_cli.runtime.context import Services

TWO_PROFILES: Final = Settings(
    default_profile="work",
    profiles={
        "work": Profile(region=Region.EU_CENTRAL_1, workspace_id="ws-1", email="me@work.test"),
        "home": Profile(),
    },
)


def test_path_prints_settings_location(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    args = ["config", "path"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == ExitCode.OK
    assert result.stdout == f"{services.settings.path}\n"


def test_list_renders_profiles_sorted_by_name(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    services.settings.save(TWO_PROFILES)
    # Act
    result = runner.invoke(cli, ["-o", "json", "config", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [
        {"name": "home", "default": False, "region": "GLOBAL", "workspaceId": None, "email": None},
        {"name": "work", "default": True, "region": "EU_CENTRAL_1", "workspaceId": "ws-1", "email": "me@work.test"},
    ]


def test_list_renders_table_with_headers(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    services.settings.save(TWO_PROFILES)
    # Act
    result = runner.invoke(cli, ["-o", "table", "config", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "EU_CENTRAL_1" in result.stdout
    assert "Profile" in result.stdout


def test_use_switches_default_profile(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    services.settings.save(TWO_PROFILES)
    # Act
    result = runner.invoke(cli, ["config", "use", "home"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.settings.load() == TWO_PROFILES.model_copy(update={"default_profile": "home"})


def test_use_rejects_unknown_profile(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    services.settings.save(TWO_PROFILES)
    # Act
    result = runner.invoke(cli, ["config", "use", "missing"])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "Unknown profile 'missing'." in result.stderr
