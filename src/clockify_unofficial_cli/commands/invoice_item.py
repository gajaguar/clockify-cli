from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import InvoiceApplyTaxes
from clockify import InvoiceFilterContains
from clockify import InvoiceIdFilter
from clockify import InvoiceImportTimeGroupType
from clockify import InvoiceItemCreate
from clockify import InvoiceItemsImport

from clockify_unofficial_cli.output.columns import INVOICE_DETAILS
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.money import to_minor_units
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_invoice
from clockify_unofficial_cli.services.resolve import resolve_project

APP: Final = typer.Typer(help="Add, import and remove invoice items.", no_args_is_help=True)

_INVOICE_ARGUMENT: Final = typer.Argument(metavar="INVOICE", help="Invoice ID or exact number.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _AddOptions:
    invoice: Annotated[str, _INVOICE_ARGUMENT]
    description: Annotated[str, typer.Option("--description", help="What the item bills for.")]
    unit_price: Annotated[float, typer.Option("--unit-price", help="Price per unit, e.g. 120.50.")]
    quantity: Annotated[int, typer.Option("--quantity", min=1, help="Number of units.")] = 1
    item_type: Annotated[str, typer.Option("--item-type", help="Item type label, e.g. Service.")] = "Service"
    apply_taxes: Annotated[
        InvoiceApplyTaxes,
        typer.Option("--apply-taxes", case_sensitive=False, help="NONE, TAX1, TAX2 or TAX1TAX2."),
    ] = InvoiceApplyTaxes.NONE


@APP.command(help="Add an item to an invoice.")
@handle_errors
@options_from(_AddOptions)
def add(ctx: typer.Context, options: _AddOptions) -> None:
    app_context = get_app_context(ctx)
    payload = InvoiceItemCreate(
        description=options.description,
        item_type=options.item_type,
        quantity=options.quantity,
        unit_price=to_minor_units(options.unit_price),
        apply_taxes=options.apply_taxes,
    )
    invoice_id = resolve_invoice(app_context, options.invoice)
    app_context.render(single(app_context.workspace().invoice_items.add(invoice_id, payload), INVOICE_DETAILS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _ImportOptions:
    invoice: Annotated[str, _INVOICE_ARGUMENT]
    start: Annotated[str, typer.Option("--from", help="Import entries from this instant.")]
    end: Annotated[str, typer.Option("--to", help="Import entries up to this instant.")]
    projects: Annotated[list[str] | None, typer.Option("--project", "-P", help="Only these projects; repeatable.")] = (
        None
    )
    expenses: Annotated[bool, typer.Option("--expenses", help="Also import expenses.")] = False
    group_type: Annotated[
        InvoiceImportTimeGroupType,
        typer.Option("--group-type", case_sensitive=False, help="SINGLE_ITEM, GROUPED or DETAILED."),
    ] = InvoiceImportTimeGroupType.GROUPED
    round_durations: Annotated[
        bool,
        typer.Option("--round-durations", help="Round entry durations the way the workspace does."),
    ] = False


@APP.command(name="import", help="Import time entries (and optionally expenses) as invoice items.")
@handle_errors
@options_from(_ImportOptions)
def import_entries(ctx: typer.Context, options: _ImportOptions) -> None:
    app_context = get_app_context(ctx)
    projects = [resolve_project(app_context, term) for term in options.projects or []]
    project_filter = (
        InvoiceIdFilter(ids=projects, contains=InvoiceFilterContains.CONTAINS) if projects else InvoiceIdFilter()
    )
    fields: dict[str, object] = {"round_time_entry_duration": True} if options.round_durations else {}
    payload = InvoiceItemsImport.model_validate({
        "from": parse_instant(options.start),
        "to": parse_instant(options.end),
        "import_expenses": options.expenses,
        "project_filter": project_filter,
        "time_entry_group_type": options.group_type,
        **fields,
    })
    invoice_id = resolve_invoice(app_context, options.invoice)
    imported = app_context.workspace().invoice_items.import_entries(invoice_id, payload)
    app_context.render(single(imported, INVOICE_DETAILS))


# Items are identified by their position, and the ones after a deleted item move up, so a repeated
# delete removes a different item. Clockify does not retry it; neither should a script.
@APP.command(help="Delete an item by its position; the items after it are renumbered.")
@handle_errors
def delete(
    ctx: typer.Context,
    invoice: Annotated[str, _INVOICE_ARGUMENT],
    order: Annotated[int, typer.Argument(metavar="ORDER", min=1, help="Position of the item in the invoice.")],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete item {order} of invoice '{invoice}' (later items are renumbered)", assume_yes=yes)
    invoice_id = resolve_invoice(app_context, invoice)
    remaining = app_context.workspace().invoice_items.delete(invoice_id, order)
    app_context.render(single(remaining, INVOICE_DETAILS))
