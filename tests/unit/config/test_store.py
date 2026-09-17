from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

from clockify_unofficial_cli.config.paths import CONFIG_DIR_ENV_VAR
from clockify_unofficial_cli.config.paths import config_dir
from clockify_unofficial_cli.config.paths import credentials_file
from clockify_unofficial_cli.config.paths import settings_file
from clockify_unofficial_cli.config.settings import OutputFormat
from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.config.store import SettingsStore
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path


def test_missing_file_loads_default_settings(tmp_path: Path) -> None:
    # Arrange
    store = SettingsStore(tmp_path / "config.toml")
    # Act
    settings = store.load()
    # Assert
    assert settings == Settings()


def test_saved_settings_load_back_from_owner_only_file(tmp_path: Path) -> None:
    # Arrange
    store = SettingsStore(tmp_path / "config.toml")
    settings = Settings(output=OutputFormat.JSON, profiles={"work": Profile(workspace_id="ws-1")})
    # Act
    store.save(settings)
    # Assert
    assert store.load() == settings
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert store.path.read_text(encoding="utf-8") == (
        'default_profile = "default"\noutput = "json"\n\n[profiles.work]\nregion = "GLOBAL"\nworkspace_id = "ws-1"\n'
    )


def test_unknown_settings_keys_are_reported_as_configuration_error(tmp_path: Path) -> None:
    # Arrange
    store = SettingsStore(tmp_path / "config.toml")
    store.path.write_text('colour = "blue"\n', encoding="utf-8")
    # Act
    with pytest.raises(CliError) as caught:
        store.load()
    # Assert
    assert caught.value.exit_code == ExitCode.CONFIGURATION
    assert caught.value.message == f"Invalid settings in {store.path}: 1 problem(s)"


def test_config_dir_honours_environment_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv(CONFIG_DIR_ENV_VAR, str(tmp_path))
    # Act
    paths = (config_dir(), settings_file(), credentials_file())
    # Assert
    assert paths == (tmp_path, tmp_path / "config.toml", tmp_path / "credentials.toml")


def test_config_dir_defaults_to_platform_location(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv(CONFIG_DIR_ENV_VAR, raising=False)
    # Act
    directory = config_dir()
    # Assert
    assert directory.name == "clockify-cli"
