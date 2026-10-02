import re
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from typer.testing import CliRunner

from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from

RUNNER: Final = CliRunner()
ANSI: Final = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True, slots=True)
class _Options:
    name: Annotated[str, typer.Argument(help="Entry name.")]
    project: Annotated[str | None, typer.Option("--project", "-P", help="Project filter.")] = None
    billable: Annotated[bool, typer.Option("--billable/--no-billable")] = False
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None


def _build_app(seen: list[_Options]) -> typer.Typer:
    app = typer.Typer()

    @app.command()
    @handle_errors
    @options_from(_Options)
    def create(ctx: typer.Context, options: _Options) -> None:
        del ctx
        seen.append(options)

    @app.command()
    def other() -> None:
        return None

    return app


def test_options_from_builds_the_dataclass_from_cli_values() -> None:
    # Arrange
    seen: list[_Options] = []
    app = _build_app(seen)
    # Act
    result = RUNNER.invoke(app, ["create", "focus", "-P", "web", "--billable", "--tag", "a", "--tag", "b"])
    # Assert
    assert result.exit_code == 0
    assert seen == [_Options(name="focus", project="web", billable=True, tag=["a", "b"])]


def test_options_from_applies_dataclass_defaults() -> None:
    # Arrange
    seen: list[_Options] = []
    app = _build_app(seen)
    # Act
    result = RUNNER.invoke(app, ["create", "focus"])
    # Assert
    assert result.exit_code == 0
    assert seen == [_Options(name="focus", project=None, billable=False, tag=None)]


def test_options_from_exposes_every_field_in_help() -> None:
    # Arrange
    app = _build_app([])
    # Act
    result = RUNNER.invoke(app, ["create", "--help"])
    # Assert
    assert result.exit_code == 0
    plain = ANSI.sub("", result.output)
    for flag in ("--project", "-P", "--billable", "--no-billable", "--tag", "Project filter."):
        assert flag in plain


def test_options_from_requires_arguments_without_defaults() -> None:
    # Arrange
    app = _build_app([])
    # Act
    result = RUNNER.invoke(app, ["create"])
    # Assert
    assert result.exit_code == 2


@dataclass(frozen=True, slots=True)
class _Base:
    project: Annotated[str | None, typer.Option("--project", "-P", help="Project filter.")] = None


@dataclass(frozen=True, slots=True)
class _Child(_Base):
    limit: Annotated[int | None, typer.Option("--limit")] = None


def _child_app(seen: list[_Child]) -> typer.Typer:
    app = typer.Typer()

    @app.command()
    @options_from(_Child)
    def run(ctx: typer.Context, options: _Child) -> None:
        del ctx
        seen.append(options)

    @app.command()
    def other() -> None:
        return None

    return app


def test_options_from_includes_fields_inherited_from_a_base_dataclass() -> None:
    # Arrange
    seen: list[_Child] = []
    app = _child_app(seen)
    # Act
    result = RUNNER.invoke(app, ["run", "-P", "web", "--limit", "3"])
    # Assert
    assert result.exit_code == 0
    assert seen == [_Child(project="web", limit=3)]
