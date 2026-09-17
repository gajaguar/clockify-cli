from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from clockify_unofficial_cli.config.paths import CONFIG_DIR_ENV_VAR
from clockify_unofficial_cli.main import create_app
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("CLOCKIFY_TEST_API_KEY"), reason="CLOCKIFY_TEST_API_KEY is not set")
def test_auth_status_reports_real_user(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv(CONFIG_DIR_ENV_VAR, str(tmp_path))
    monkeypatch.setenv("CLOCKIFY_API_KEY", os.environ["CLOCKIFY_TEST_API_KEY"])
    # Act
    result = CliRunner().invoke(create_app(), ["-o", "json", "auth", "status"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["source"] == "environment"
