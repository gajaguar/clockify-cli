import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import Webhook
from clockify import WebhookCreate
from clockify import WebhookDeliveryStatus
from clockify import WebhookEvent
from clockify import WebhookLogSearch
from clockify import WebhookLogStatus
from clockify import WebhookTriggerSourceType
from clockify import WebhookType
from clockify import WebhookUpdate

from clockify_unofficial_cli.output.columns import WEBHOOKS
from clockify_unofficial_cli.output.columns import WEBHOOKS_WITH_TOKEN
from clockify_unofficial_cli.output.columns import WEBHOOK_LOGS
from clockify_unofficial_cli.output.columns import WEBHOOK_STATUSES
from clockify_unofficial_cli.output.renderer import Record
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.output.renderer import to_record
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_webhook

APP: Final = typer.Typer(help="Manage workspace webhooks and inspect their deliveries.", no_args_is_help=True)

_TOKEN_KEY: Final = "authToken"  # ruff: ignore[hardcoded-password-string]  JSON field name, not a secret


# The signing token proves a delivery came from Clockify, so only the commands that exist to hand
# it over (create, rotate-token) print it; list, get and update drop it from every output format.
def _without_token(webhook: Webhook) -> Record:
    return {key: value for key, value in to_record(webhook).items() if key != _TOKEN_KEY}


# A name left unset must stay out of the request body; an explicit None would be sent as null.
def _name_field(name: str | None) -> dict[str, str]:
    return {} if name is None else {"name": name}


@APP.command(name="list", help="List the workspace webhooks.")
@handle_errors
def list_webhooks(
    ctx: typer.Context,
    *,
    webhook_type: Annotated[
        WebhookType | None,
        typer.Option("--type", case_sensitive=False, help="Only webhooks of this type."),
    ] = None,
    addon: Annotated[
        str | None,
        typer.Option("--addon", help="List the webhooks owned by this add-on ID instead."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    webhooks = app_context.workspace().webhooks
    found = webhooks.list_for_addon(addon) if addon is not None else webhooks.list(webhook_type=webhook_type)
    app_context.render(many([_without_token(item) for item in found], WEBHOOKS))


@APP.command(help="Show a webhook by ID or exact name.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")]) -> None:
    app_context = get_app_context(ctx)
    webhook = app_context.workspace().webhooks.get(resolve_webhook(app_context, term))
    app_context.render(single(_without_token(webhook), WEBHOOKS))


@dataclass(frozen=True, slots=True)
class _CreateOptions:
    url: Annotated[str, typer.Option("--url", help="Endpoint Clockify calls on each event.")]
    event: Annotated[WebhookEvent, typer.Option("--event", case_sensitive=False, help="Event that triggers it.")]
    name: Annotated[str | None, typer.Option("--name", help="Webhook name.")] = None
    source_type: Annotated[
        WebhookTriggerSourceType,
        typer.Option("--source-type", case_sensitive=False, help="What --source identifies."),
    ] = WebhookTriggerSourceType.WORKSPACE_ID
    source: Annotated[
        list[str] | None,
        typer.Option("--source", help="Trigger source ID; repeatable. Defaults to the workspace."),
    ] = None


@APP.command(help="Create a webhook; prints its signing token once.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    payload = WebhookCreate(
        url=options.url,
        webhook_event=options.event,
        trigger_source=options.source or [str(workspace.id)],
        trigger_source_type=options.source_type,
        **_name_field(options.name),
    )
    app_context.render(single(workspace.webhooks.create(payload), WEBHOOKS_WITH_TOKEN))


@dataclass(frozen=True, slots=True)
class _UpdateOptions:
    term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")]
    url: Annotated[str | None, typer.Option("--url", help="New endpoint.")] = None
    event: Annotated[
        WebhookEvent | None,
        typer.Option("--event", case_sensitive=False, help="New triggering event."),
    ] = None
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None
    source_type: Annotated[
        WebhookTriggerSourceType | None,
        typer.Option("--source-type", case_sensitive=False, help="New source type."),
    ] = None
    source: Annotated[
        list[str] | None,
        typer.Option("--source", help="Replace the trigger sources; repeatable."),
    ] = None


# Clockify's PUT needs every field, so unset options keep the stored value.
@APP.command(help="Update a webhook; options left out keep their current value.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    webhooks = app_context.workspace().webhooks
    webhook_id = resolve_webhook(app_context, options.term)
    current = webhooks.get(webhook_id)
    payload = WebhookUpdate(
        url=options.url or current.url,
        webhook_event=options.event or current.webhook_event,
        trigger_source=options.source or current.trigger_source,
        trigger_source_type=options.source_type or current.trigger_source_type,
        **_name_field(options.name if options.name is not None else current.name),
    )
    app_context.render(single(_without_token(webhooks.update(webhook_id, payload)), WEBHOOKS))


@APP.command(help="Delete a webhook.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete webhook '{term}'", assume_yes=yes)
    webhook_id = resolve_webhook(app_context, term)
    app_context.workspace().webhooks.delete(webhook_id)
    app_context.notify(f"Deleted webhook '{webhook_id}'.")


@APP.command(name="rotate-token", help="Issue a new signing token; the old one stops working.")
@handle_errors
def rotate_token(
    ctx: typer.Context,
    term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Rotate the signing token of webhook '{term}'", assume_yes=yes)
    webhook = app_context.workspace().webhooks.regenerate_token(resolve_webhook(app_context, term))
    app_context.render(single(webhook, WEBHOOKS_WITH_TOKEN))


@dataclass(frozen=True, slots=True)
class _LogsOptions:
    term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")]
    status: Annotated[
        WebhookLogStatus | None,
        typer.Option("--status", case_sensitive=False, help="Only deliveries with this outcome."),
    ] = None
    start: Annotated[str | None, typer.Option("--from", help="Only deliveries after this instant.")] = None
    end: Annotated[str | None, typer.Option("--to", help="Only deliveries before this instant.")] = None
    newest_first: Annotated[bool, typer.Option("--newest-first", help="Sort the newest delivery first.")] = False
    limit: Annotated[int | None, typer.Option("--limit", help="Stop after N entries; not with --page.")] = None
    page: Annotated[int | None, typer.Option("--page", help="1-based page number.")] = None
    page_size: Annotated[int | None, typer.Option("--page-size", help="Page size.")] = None


@APP.command(help="List the delivery attempts of a webhook.")
@handle_errors
@options_from(_LogsOptions)
def logs(ctx: typer.Context, options: _LogsOptions) -> None:
    app_context = get_app_context(ctx)
    webhooks = app_context.workspace().webhooks
    webhook_id = resolve_webhook(app_context, options.term)
    fields = {
        "from": parse_instant(options.start) if options.start else None,
        "to": parse_instant(options.end) if options.end else None,
        "status": options.status,
        "sortByNewest": True if options.newest_first else None,
    }
    search = WebhookLogSearch.model_validate({key: value for key, value in fields.items() if value is not None})
    entries = list_from_options(
        functools.partial(webhooks.logs, webhook_id, search=search),
        functools.partial(webhooks.logs_page, webhook_id, search=search),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(entries, WEBHOOK_LOGS))


@dataclass(frozen=True, slots=True)
class _StatusesOptions:
    term: Annotated[str, typer.Argument(help="Webhook ID or exact name.")]
    status: Annotated[
        WebhookDeliveryStatus | None,
        typer.Option("--status", case_sensitive=False, help="Only events with this delivery status."),
    ] = None
    limit: Annotated[int | None, typer.Option("--limit", help="Stop after N entries; not with --page.")] = None
    page: Annotated[int | None, typer.Option("--page", help="1-based page number.")] = None
    page_size: Annotated[int | None, typer.Option("--page-size", help="Page size.")] = None


@APP.command(help="List the delivery status of each event sent to a webhook.")
@handle_errors
@options_from(_StatusesOptions)
def statuses(ctx: typer.Context, options: _StatusesOptions) -> None:
    app_context = get_app_context(ctx)
    webhooks = app_context.workspace().webhooks
    webhook_id = resolve_webhook(app_context, options.term)
    entries = list_from_options(
        functools.partial(webhooks.statuses, webhook_id, status=options.status),
        functools.partial(webhooks.statuses_page, webhook_id, status=options.status),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(entries, WEBHOOK_STATUSES))
