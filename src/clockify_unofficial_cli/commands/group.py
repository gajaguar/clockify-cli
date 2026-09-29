import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import UserGroupCreate
from clockify import UserGroupUpdate

from clockify_unofficial_cli.output.columns import GROUPS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_group

APP: Final = typer.Typer(help="Manage workspace user groups.", no_args_is_help=True)


@APP.command(name="list", help="List every user group in the active workspace.")
@handle_errors
def list_groups(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N groups; incompatible with --page/--page-size."),
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
    groups = list_from_options(workspace.user_groups.list, workspace.user_groups.list_page, limit, page, page_size)
    app_context.render(many(groups, GROUPS))


@APP.command(help="Create a new user group.")
@handle_errors
def create(ctx: typer.Context, *, name: Annotated[str, typer.Option("--name", help="Group name.")]) -> None:
    app_context = get_app_context(ctx)
    group = app_context.workspace().user_groups.create(UserGroupCreate(name=name))
    app_context.render(single(group, GROUPS))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    name: str


@APP.command(help="Update an existing user group.")
@handle_errors
def update(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Group ID or exact name.")],
    *,
    name: Annotated[str, typer.Option("--name", help="New group name.")],
) -> None:
    args = _UpdateArgs(name=name)
    app_context = get_app_context(ctx)
    group_id = resolve_group(app_context, term)
    group = app_context.workspace().user_groups.update(group_id, UserGroupUpdate(**dataclasses.asdict(args)))
    app_context.render(single(group, GROUPS))


@APP.command(help="Delete a user group.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Group ID or exact name.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete user group '{term}'", assume_yes=yes)
    group_id = resolve_group(app_context, term)
    app_context.workspace().user_groups.delete(group_id)
    app_context.notify(f"Deleted user group '{group_id}'.")
