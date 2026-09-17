import dataclasses
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import CustomFieldCreate
from clockify import CustomFieldUpdate

from clockify_unofficial_cli.output.columns import CUSTOM_FIELDS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_custom_field

APP: Final = typer.Typer(help="Manage workspace custom fields.", no_args_is_help=True)


@APP.command(name="list", help="List every custom field in the active workspace.")
@handle_errors
def list_custom_fields(
    ctx: typer.Context,
    *,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Stop after N fields; incompatible with --page/--page-size."),
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
    fields = list_from_options(workspace.custom_fields.list, workspace.custom_fields.list_page, limit, page, page_size)
    app_context.render(many(fields, CUSTOM_FIELDS))


@dataclass(frozen=True, slots=True)
class _CreateArgs:  # pylint: disable=too-many-instance-attributes
    name: str
    type: str
    entity_type: str | None
    allowed_values: list[str] | None
    workspace_default_value: str | None
    placeholder: str | None
    description: str | None
    status: str | None
    only_admin_can_edit: bool | None


@APP.command(help="Create a new custom field.")
@handle_errors
def create(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    name: Annotated[str, typer.Option("--name", help="Field display name.")],
    type: Annotated[  # noqa: A002  pylint: disable=redefined-builtin
        str, typer.Option("--type", help="Clockify field type, e.g. TXT or NUMBER.")
    ],
    entity_type: Annotated[
        str | None,
        typer.Option("--entity", help="Entity the field belongs to, e.g. TIMEENTRY."),
    ] = None,
    allowed_values: Annotated[
        list[str] | None,
        typer.Option(
            "--allowed-value",
            help="Allowed value for dropdown fields; pass multiple times.",
        ),
    ] = None,
    workspace_default_value: Annotated[
        str | None,
        typer.Option("--default-value", help="Default value applied to new entities."),
    ] = None,
    placeholder: Annotated[
        str | None,
        typer.Option("--placeholder", help="Placeholder shown in the input."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", help="Free-form description."),
    ] = None,
    status: Annotated[
        str | None,
        typer.Option("--status", help="VISIBLE, INVISIBLE or INACTIVE."),
    ] = None,
    only_admin_can_edit: Annotated[
        bool | None,
        typer.Option("--admin-only/--open", help="Only admins may edit the field."),
    ] = None,
) -> None:
    args = _CreateArgs(
        name=name,
        type=type,
        entity_type=entity_type,
        allowed_values=allowed_values,
        workspace_default_value=workspace_default_value,
        placeholder=placeholder,
        description=description,
        status=status,
        only_admin_can_edit=only_admin_can_edit,
    )
    app_context = get_app_context(ctx)
    payload = CustomFieldCreate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    field = app_context.workspace().custom_fields.create(payload)
    app_context.render(single(field, CUSTOM_FIELDS))


@dataclass(frozen=True, slots=True)
class _UpdateArgs:  # pylint: disable=too-many-instance-attributes
    name: str | None
    allowed_values: list[str] | None
    workspace_default_value: str | None
    placeholder: str | None
    description: str | None
    status: str | None
    required: bool | None
    only_admin_can_edit: bool | None


@APP.command(help="Update an existing custom field.")
@handle_errors
def update(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Custom field ID or exact name.")],
    *,
    name: Annotated[
        str | None,
        typer.Option("--name", help="New field display name."),
    ] = None,
    allowed_values: Annotated[
        list[str] | None,
        typer.Option("--allowed-value", help="New dropdown values; pass multiple times."),
    ] = None,
    workspace_default_value: Annotated[
        str | None,
        typer.Option("--default-value", help="New default value."),
    ] = None,
    placeholder: Annotated[
        str | None,
        typer.Option("--placeholder", help="New placeholder."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", help="New description."),
    ] = None,
    status: Annotated[
        str | None,
        typer.Option("--status", help="VISIBLE, INVISIBLE or INACTIVE."),
    ] = None,
    required: Annotated[
        bool | None,
        typer.Option("--required/--optional", help="Toggle whether the field is required."),
    ] = None,
    only_admin_can_edit: Annotated[
        bool | None,
        typer.Option("--admin-only/--open", help="Restrict edits to admins."),
    ] = None,
) -> None:
    args = _UpdateArgs(
        name=name,
        allowed_values=allowed_values,
        workspace_default_value=workspace_default_value,
        placeholder=placeholder,
        description=description,
        status=status,
        required=required,
        only_admin_can_edit=only_admin_can_edit,
    )
    app_context = get_app_context(ctx)
    field_id = resolve_custom_field(app_context, term)
    payload = CustomFieldUpdate(**{k: v for k, v in dataclasses.asdict(args).items() if v is not None})
    field = app_context.workspace().custom_fields.update(field_id, payload)
    app_context.render(single(field, CUSTOM_FIELDS))


@APP.command(help="Delete a custom field.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Custom field ID or exact name.")],
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete custom field '{term}'", assume_yes=yes)
    field_id = resolve_custom_field(app_context, term)
    app_context.workspace().custom_fields.delete(field_id)
    app_context.notify(f"Deleted custom field '{field_id}'.")
