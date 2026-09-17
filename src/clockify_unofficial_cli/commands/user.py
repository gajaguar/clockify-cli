from typing import Annotated
from typing import Final

import typer

from clockify_unofficial_cli.output.columns import USERS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.services.listing import list_from_options

APP: Final = typer.Typer(help="Show the authenticated user and workspace members.", no_args_is_help=True)


@APP.command(help="Show the API key owner.")
@handle_errors
def me(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    user = app_context.client().user.me()
    app_context.render(single(user, USERS))


@APP.command(name="list", help="List every user visible in the active workspace.")
@handle_errors
def list_users(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N users; incompatible with --page/--page-size."),
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
    users = list_from_options(workspace.users.list, workspace.users.list_page, limit, page, page_size)
    app_context.render(many(users, USERS))
