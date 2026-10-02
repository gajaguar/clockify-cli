from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import InvoiceTaxType

from clockify_unofficial_cli.output.columns import INVOICE_SETTINGS
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.services.invoices import SettingsChanges
from clockify_unofficial_cli.services.invoices import build_settings_update
from clockify_unofficial_cli.services.invoices import check_export_fields
from clockify_unofficial_cli.services.invoices import parse_labels

APP: Final = typer.Typer(help="Read and change the workspace's invoice settings.", no_args_is_help=True)


@APP.command(help="Show the workspace's invoice defaults, labels and export fields.")
@handle_errors
def get(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.workspace().invoices.get_settings(), INVOICE_SETTINGS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    notes: Annotated[str | None, typer.Option("--notes", help="Default invoice notes.")] = None
    subject: Annotated[str | None, typer.Option("--subject", help="Default invoice subject.")] = None
    due_days: Annotated[int | None, typer.Option("--due-days", help="Days until an invoice is due.")] = None
    tax_percent: Annotated[float | None, typer.Option("--tax", help="Default tax percentage.")] = None
    tax2_percent: Annotated[float | None, typer.Option("--tax2", help="Default second tax percentage.")] = None
    tax_type: Annotated[
        InvoiceTaxType | None,
        typer.Option("--tax-type", case_sensitive=False, help="COMPOUND, SIMPLE or NONE."),
    ] = None
    company_id: Annotated[str | None, typer.Option("--company", help="Default company ID.")] = None
    labels: Annotated[
        list[str] | None,
        typer.Option("--label", help="Rename a label as NAME=TEXT, e.g. due_date=Pay by; repeatable."),
    ] = None
    show: Annotated[
        list[str] | None,
        typer.Option("--show", help="Show an export field: item_type, quantity, unit_price, tax, tax2 or rtl."),
    ] = None
    hide: Annotated[list[str] | None, typer.Option("--hide", help="Hide an export field; repeatable.")] = None


# The PUT needs every label, so the stored settings are read first and sent back with the changes.
@APP.command(help="Update the invoice settings; options left out keep their current value.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    invoices = app_context.workspace().invoices
    check_export_fields([*(options.show or []), *(options.hide or [])])
    changes = SettingsChanges(
        notes=options.notes,
        subject=options.subject,
        due_days=options.due_days,
        tax_percent=options.tax_percent,
        tax2_percent=options.tax2_percent,
        tax_type=options.tax_type,
        company_id=options.company_id,
        labels=parse_labels(options.labels or []),
        show=options.show or [],
        hide=options.hide or [],
    )
    payload = build_settings_update(invoices.get_settings(), changes)
    app_context.render(single(invoices.update_settings(payload), INVOICE_SETTINGS))
