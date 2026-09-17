from __future__ import annotations

from typing import Final

import pytest
from clockify import Region

from clockify_unofficial_cli.config.settings import GlobalOptions
from clockify_unofficial_cli.config.settings import OutputFormat
from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import ResolvedOptions
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.config.settings import resolve_options

WORK: Final = Profile(region=Region.EU_CENTRAL_1, workspace_id="ws-work")
SETTINGS: Final = Settings(default_profile="work", output=OutputFormat.CSV, profiles={"work": WORK})


def test_settings_values_apply_when_no_flags_are_given() -> None:
    # Arrange
    options = GlobalOptions()
    # Act
    resolved = resolve_options(options, SETTINGS, is_tty=True)
    # Assert
    assert resolved == ResolvedOptions(
        profile_name="work", profile=WORK, workspace_id="ws-work", output=OutputFormat.CSV
    )


def test_flags_override_settings() -> None:
    # Arrange
    options = GlobalOptions(profile="home", workspace="ws-flag", output=OutputFormat.ID)
    # Act
    resolved = resolve_options(options, SETTINGS, is_tty=True)
    # Assert
    assert resolved == ResolvedOptions(
        profile_name="home", profile=Profile(), workspace_id="ws-flag", output=OutputFormat.ID
    )


@pytest.mark.parametrize(("is_tty", "expected"), [(True, OutputFormat.TABLE), (False, OutputFormat.JSON)])
def test_output_falls_back_to_table_on_terminals_and_json_on_pipes(is_tty: bool, expected: OutputFormat) -> None:
    # Arrange
    settings = Settings()
    # Act
    resolved = resolve_options(GlobalOptions(), settings, is_tty=is_tty)
    # Assert
    assert resolved.output == expected


def test_profiles_can_be_added_and_removed_without_mutating_original() -> None:
    # Arrange
    original = Settings()
    # Act
    added = original.with_profile("work", WORK)
    removed = added.without_profile("work")
    # Assert
    assert original == Settings()
    assert added == Settings(profiles={"work": WORK})
    assert removed == Settings()
