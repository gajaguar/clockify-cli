import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ClientId
from clockify import ProjectCreate
from clockify import ProjectUpdate

from clockify_unofficial_cli.output.columns import PROJECTS_LIST
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_client
from clockify_unofficial_cli.services.resolve import resolve_project

APP: Final = typer.Typer(help="Manage workspace projects.", no_args_is_help=True)


@APP.command(name="list", help="List every project in the active workspace.")
@handle_errors
def list_projects(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N projects; incompatible with --page/--page-size."),
    ] = None,
    page: Annotated[
        int | None,
        typer.Option("--page", help="1-based page number when paging through results."),
    ] = None,
    page_size: Annotated[
        int | None,
        typer.Option("--page-size", help="Page size when paging through results."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    projects = list_from_options(workspace.projects.list, workspace.projects.list_page, limit, page, page_size)
    app_context.render(many(projects, PROJECTS_LIST))


@APP.command(help="Show a project by ID or exact name.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, typer.Argument(help="Project ID or exact name.")]) -> None:
    app_context = get_app_context(ctx)
    project_id = resolve_project(app_context, term)
    project = app_context.workspace().projects.get(project_id)
    app_context.render(single(project, PROJECTS_LIST))


@dataclass(frozen=True, slots=True)
class _CreateArgs:
    name: str
    client_id: ClientId | None
    is_public: bool | None
    billable: bool | None
    color: str | None
    note: str | None


@APP.command(help="Create a new project.")
@handle_errors
def create(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    name: Annotated[str, typer.Option("--name", help="Project display name.")],
    client: Annotated[
        str | None,
        typer.Option("--client", help="Client ID or exact name; pass --no-client to leave it blank."),
    ] = None,
    public: Annotated[
        bool | None,
        typer.Option(
            "--public/--private",
            help="Whether the project is visible to every workspace member; omit to leave the default.",
        ),
    ] = None,
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--no-billable", help="Default billable flag for time entries."),
    ] = None,
    color: Annotated[
        str | None,
        typer.Option("--color", help="Hex colour, e.g. #0f62fe."),
    ] = None,
    note: Annotated[
        str | None,
        typer.Option("--note", help="Free-form note."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    client_id: ClientId | None = ClientId(resolve_client(app_context, client)) if client else None
    args = _CreateArgs(
        name=name,
        client_id=client_id,
        is_public=public,
        billable=billable,
        color=color,
        note=note,
    )
    payload = ProjectCreate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    project = app_context.workspace().projects.create(payload)
    app_context.render(single(project, PROJECTS_LIST))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    name: str | None
    client_id: ClientId | None
    is_public: bool | None
    billable: bool | None
    color: str | None
    note: str | None
    archived: bool | None


@APP.command(help="Update an existing project.")
@handle_errors
def update(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Project ID or exact name.")],
    *,
    name: Annotated[
        str | None,
        typer.Option("--name", help="New project display name."),
    ] = None,
    client: Annotated[
        str | None,
        typer.Option("--client", help="New client ID or exact name."),
    ] = None,
    public: Annotated[
        bool | None,
        typer.Option("--public/--private", help="Toggle the project's visibility."),
    ] = None,
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--no-billable", help="Default billable flag for new entries."),
    ] = None,
    color: Annotated[
        str | None,
        typer.Option("--color", help="Hex colour, e.g. #0f62fe."),
    ] = None,
    note: Annotated[
        str | None,
        typer.Option("--note", help="New free-form note."),
    ] = None,
    archived: Annotated[
        bool | None,
        typer.Option("--archived/--no-archived", help="Archive or restore the project."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    project_id = resolve_project(app_context, term)
    client_id: ClientId | None = ClientId(resolve_client(app_context, client)) if client else None
    args = _UpdateArgs(
        name=name,
        client_id=client_id,
        is_public=public,
        billable=billable,
        color=color,
        note=note,
        archived=archived,
    )
    payload = ProjectUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    project = app_context.workspace().projects.update(project_id, payload)
    app_context.render(single(project, PROJECTS_LIST))


@APP.command(help="Delete a project.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Project ID or exact name.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete project '{term}'", assume_yes=yes)
    project_id = resolve_project(app_context, term)
    app_context.workspace().projects.delete(project_id)
    app_context.notify(f"Deleted project '{project_id}'.")
