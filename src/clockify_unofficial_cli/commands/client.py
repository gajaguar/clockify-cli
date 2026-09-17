import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ClientCreate
from clockify import ClientUpdate

from clockify_unofficial_cli.output.columns import CLIENTS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_client

APP: Final = typer.Typer(help="Manage workspace clients.", no_args_is_help=True)


@APP.command(name="list", help="List every client in the active workspace.")
@handle_errors
def list_clients(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N clients; incompatible with --page/--page-size."),
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
    clients = list_from_options(workspace.clients.list, workspace.clients.list_page, limit, page, page_size)
    app_context.render(many(clients, CLIENTS))


@APP.command(help="Show a client by ID or exact name.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, typer.Argument(help="Client ID or exact name.")]) -> None:
    app_context = get_app_context(ctx)
    client_id = resolve_client(app_context, term)
    client = app_context.workspace().clients.get(client_id)
    app_context.render(single(client, CLIENTS))


@dataclass(frozen=True, slots=True)
class _CreateArgs:
    name: str
    email: str | None
    address: str | None
    note: str | None


@APP.command(help="Create a new client.")
@handle_errors
def create(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    name: Annotated[str, typer.Option("--name", help="Client display name.")],
    email: Annotated[
        str | None,
        typer.Option("--email", help="Contact email."),
    ] = None,
    address: Annotated[
        str | None,
        typer.Option("--address", help="Postal address."),
    ] = None,
    note: Annotated[
        str | None,
        typer.Option("--note", help="Free-form note."),
    ] = None,
) -> None:
    args = _CreateArgs(name=name, email=email, address=address, note=note)
    app_context = get_app_context(ctx)
    payload = ClientCreate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    client = app_context.workspace().clients.create(payload)
    app_context.render(single(client, CLIENTS))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    name: str | None
    email: str | None
    address: str | None
    note: str | None
    archived: bool | None


@APP.command(help="Update an existing client.")
@handle_errors
def update(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Client ID or exact name.")],
    *,
    name: Annotated[
        str | None,
        typer.Option("--name", help="New client display name."),
    ] = None,
    email: Annotated[
        str | None,
        typer.Option("--email", help="New contact email."),
    ] = None,
    address: Annotated[
        str | None,
        typer.Option("--address", help="New postal address."),
    ] = None,
    note: Annotated[
        str | None,
        typer.Option("--note", help="New free-form note."),
    ] = None,
    archived: Annotated[
        bool | None,
        typer.Option(
            "--archived/--no-archived",
            help="Archive or restore the client; omit the flag to leave the field untouched.",
        ),
    ] = None,
) -> None:
    args = _UpdateArgs(name=name, email=email, address=address, note=note, archived=archived)
    app_context = get_app_context(ctx)
    client_id = resolve_client(app_context, term)
    payload = ClientUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    client = app_context.workspace().clients.update(client_id, payload)
    app_context.render(single(client, CLIENTS))


@APP.command(help="Delete a client.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Client ID or exact name.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete client '{term}'", assume_yes=yes)
    client_id = resolve_client(app_context, term)
    app_context.workspace().clients.delete(client_id)
    app_context.notify(f"Deleted client '{client_id}'.")
