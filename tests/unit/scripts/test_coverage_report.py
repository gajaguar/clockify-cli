from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import pytest

from scripts.coverage_report import CoverageReport
from scripts.coverage_report import build_report
from scripts.coverage_report import format_report
from scripts.coverage_report import main
from scripts.coverage_report import spec_operations
from scripts.coverage_report import table_statuses

if TYPE_CHECKING:
    from pathlib import Path

SPEC: Final = {
    "paths": {
        "/v1/user": {"get": {"summary": "me"}, "parameters": []},
        "/v1/workspaces": {"get": {}, "post": {"deprecated": True}},
        "/v1/broken": "not a mapping",
    }
}

TABLE: Final = """
| Endpoint | SDK method | CLI command | Phase | Status |
| --- | --- | --- | --- | --- |
| `GET /user` | `client.user.me()` | `clockify user me` | 1 | done |
| `DELETE /gone` |  | `clockify gone` | 2 | planned |
"""


def test_spec_operations_skip_deprecated_and_non_operations() -> None:
    # Arrange
    spec = SPEC
    # Act
    operations = spec_operations(spec)
    # Assert
    assert operations == frozenset({"GET /user", "GET /workspaces"})


def test_spec_without_paths_has_no_operations() -> None:
    # Arrange
    spec: dict[str, object] = {}
    # Act
    operations = spec_operations(spec)
    # Assert
    assert operations == frozenset()


def test_report_flags_missing_and_unknown_rows() -> None:
    # Arrange
    statuses = table_statuses(TABLE)
    # Act
    report = build_report(spec_operations(SPEC), statuses)
    # Assert
    assert report == CoverageReport(total=2, done=1, missing=("GET /workspaces",), unknown=("DELETE /gone",))
    assert report.complete is False
    assert format_report(report) == (
        "CLI coverage: 1/2 operations done (50%)\n"
        "missing from coverage table: GET /workspaces\n"
        "not in the OpenAPI spec (removed or deprecated upstream?): DELETE /gone\n"
    )


@pytest.mark.parametrize(
    ("status", "strict", "expected"),
    [("done", True, 0), ("planned", False, 0), ("planned", True, 1)],
)
def test_main_exit_code_depends_on_completeness(tmp_path: Path, status: str, strict: bool, expected: int) -> None:
    # Arrange
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(json.dumps({"paths": {"/v1/user": {"get": {}}}}), encoding="utf-8")
    coverage_path = tmp_path / "coverage.md"
    coverage_path.write_text(f"| `GET /user` | | `clockify user me` | 1 | {status} |\n", encoding="utf-8")
    args = ["--spec", str(spec_path), "--coverage", str(coverage_path), *(["--strict"] if strict else [])]
    # Act
    exit_code = main(args)
    # Assert
    assert exit_code == expected


def test_main_fails_when_table_is_out_of_sync(tmp_path: Path) -> None:
    # Arrange
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(json.dumps(SPEC), encoding="utf-8")
    coverage_path = tmp_path / "coverage.md"
    coverage_path.write_text(TABLE, encoding="utf-8")
    # Act
    exit_code = main(["--spec", str(spec_path), "--coverage", str(coverage_path)])
    # Assert
    assert exit_code == 1
