import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import TagCreate
from clockify import TagUpdate

from clockify_unofficial_cli.output.columns import TAGS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_tag

APP: Final = typer.Typer(help="Manage workspace tags.", no_args_is_help=True)


@APP.command(name="list", help="List every tag in the active workspace.")
@handle_errors
def list_tags(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N tags; incompatible with --page/--page-size."),
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
    tags = list_from_options(workspace.tags.list, workspace.tags.list_page, limit, page, page_size)
    app_context.render(many(tags, TAGS))


@APP.command(help="Show a tag by ID or exact name.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, typer.Argument(help="Tag ID or exact name.")]) -> None:
    app_context = get_app_context(ctx)
    tag_id = resolve_tag(app_context, term)
    tag = app_context.workspace().tags.get(tag_id)
    app_context.render(single(tag, TAGS))


@APP.command(help="Create a new tag.")
@handle_errors
def create(ctx: typer.Context, *, name: Annotated[str, typer.Option("--name", help="Tag name.")]) -> None:
    app_context = get_app_context(ctx)
    tag = app_context.workspace().tags.create(TagCreate(name=name))
    app_context.render(single(tag, TAGS))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:
    name: str | None
    archived: bool | None


@APP.command(help="Update an existing tag.")
@handle_errors
def update(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Tag ID or exact name.")],
    *,
    name: Annotated[
        str | None,
        typer.Option("--name", help="New tag name."),
    ] = None,
    archived: Annotated[
        bool | None,
        typer.Option("--archived/--no-archived", help="Archive or restore the tag."),
    ] = None,
) -> None:
    args = _UpdateArgs(name=name, archived=archived)
    app_context = get_app_context(ctx)
    tag_id = resolve_tag(app_context, term)
    payload = TagUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    tag = app_context.workspace().tags.update(tag_id, payload)
    app_context.render(single(tag, TAGS))


@APP.command(help="Delete a tag.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Tag ID or exact name.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete tag '{term}'", assume_yes=yes)
    tag_id = resolve_tag(app_context, term)
    app_context.workspace().tags.delete(tag_id)
    app_context.notify(f"Deleted tag '{tag_id}'.")
