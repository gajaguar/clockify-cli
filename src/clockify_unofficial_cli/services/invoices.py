from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

from clockify import InvoiceDefaults
from clockify import InvoiceDefaultsUpdate
from clockify import InvoiceExportFieldsUpdate
from clockify import InvoiceLabelsUpdate
from clockify import InvoiceSettingsUpdate
from clockify import InvoiceUpdate

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    import datetime
    from collections.abc import Sequence

    from clockify import InvoiceDetails
    from clockify import InvoiceSettings
    from clockify import InvoiceTaxType

EXPORT_FIELDS: Final = frozenset(InvoiceExportFieldsUpdate.model_fields)
LABEL_FIELDS: Final = frozenset(InvoiceLabelsUpdate.model_fields)
# The settings read model names this label differently from the update model.
_LABEL_RENAMES: Final = {"total_amount": "total_amount_due"}


def _required[T](value: T | None, option: str) -> T:
    if value is None:
        message = f"Clockify returned no value for this field; pass {option}."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return value


@dataclass(frozen=True, slots=True)
class InvoiceChanges:
    number: str | None = None
    currency: str | None = None
    issued_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    discount: float | None = None
    tax: float | None = None
    tax2: float | None = None
    client_id: str | None = None
    company_id: str | None = None
    note: str | None = None
    subject: str | None = None
    tax_type: InvoiceTaxType | None = None


# Clockify's PUT replaces the invoice and requires the dates and the three percentages, so anything
# the caller leaves alone is copied from the stored invoice.
def build_invoice_update(current: InvoiceDetails, changes: InvoiceChanges) -> InvoiceUpdate:
    optional: dict[str, Any] = {
        "client_id": changes.client_id or current.client_id,
        "company_id": changes.company_id or current.company_id,
        "note": changes.note if changes.note is not None else current.note,
        "subject": changes.subject if changes.subject is not None else current.subject,
        "tax_type": changes.tax_type or current.tax_type,
    }
    return InvoiceUpdate(
        currency=changes.currency or _required(current.currency, "--currency"),
        number=changes.number or _required(current.number, "--number"),
        issued_date=changes.issued_date or _required(current.issued_date, "--issued"),
        due_date=changes.due_date or _required(current.due_date, "--due"),
        discount_percent=changes.discount if changes.discount is not None else current.discount or 0.0,
        tax_percent=changes.tax if changes.tax is not None else current.tax or 0.0,
        tax2_percent=changes.tax2 if changes.tax2 is not None else current.tax2 or 0.0,
        **{key: value for key, value in optional.items() if value is not None},
    )


@dataclass(frozen=True, slots=True)
class SettingsChanges:
    notes: str | None = None
    subject: str | None = None
    due_days: int | None = None
    tax_percent: float | None = None
    tax2_percent: float | None = None
    tax_type: InvoiceTaxType | None = None
    company_id: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    show: Sequence[str] = ()
    hide: Sequence[str] = ()


def parse_labels(pairs: Sequence[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for pair in pairs:
        name, separator, value = pair.partition("=")
        key = name.strip().replace("-", "_")
        if not separator or key not in LABEL_FIELDS:
            message = f"Invalid --label '{pair}'; use NAME=TEXT with NAME one of: {', '.join(sorted(LABEL_FIELDS))}."
            raise CliError(message, exit_code=ExitCode.USAGE)
        labels[key] = value
    return labels


def check_export_fields(names: Sequence[str]) -> None:
    unknown = sorted(set(names) - EXPORT_FIELDS)
    if unknown:
        message = f"Unknown export field(s): {', '.join(unknown)}; use {', '.join(sorted(EXPORT_FIELDS))}."
        raise CliError(message, exit_code=ExitCode.USAGE)


def _labels(current: InvoiceSettings, overrides: dict[str, str]) -> InvoiceLabelsUpdate:
    stored = current.labels.model_dump(exclude_none=True) if current.labels is not None else {}
    values = {
        _LABEL_RENAMES.get(name, name): value
        for name, value in stored.items()
        if name in LABEL_FIELDS | {"total_amount"}
    }
    values.update(overrides)
    missing = sorted(LABEL_FIELDS - values.keys())
    if missing:
        message = f"Clockify returned no value for label(s) {', '.join(missing)}; pass --label NAME=TEXT for each."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return InvoiceLabelsUpdate(**values)


def _first[T](*values: T | None) -> T | None:
    return next((value for value in values if value is not None), None)


# The settings PUT requires every label and the default notes and subject, so the stored values are
# sent back with only the requested changes applied.
def build_settings_update(current: InvoiceSettings, changes: SettingsChanges) -> InvoiceSettingsUpdate:
    stored = current.defaults or InvoiceDefaults()
    fields: dict[str, Any] = {
        "notes": _first(changes.notes, stored.notes, ""),
        "subject": _first(changes.subject, stored.subject, ""),
        "due_days": _first(changes.due_days, stored.due_days),
        "company_id": _first(changes.company_id, stored.company_id),
        "item_type_id": stored.item_type_id,
        "tax_percent": _first(changes.tax_percent, stored.tax_percent),
        "tax2_percent": _first(changes.tax2_percent, stored.tax2_percent),
        "tax_type": _first(changes.tax_type, stored.tax_type),
    }
    exports = current.export_fields.model_dump(exclude_none=True) if current.export_fields is not None else {}
    exports.update(dict.fromkeys(changes.show, True) | dict.fromkeys(changes.hide, False))
    payload: dict[str, Any] = {
        "labels": _labels(current, changes.labels),
        "defaults": InvoiceDefaultsUpdate(**{key: value for key, value in fields.items() if value is not None}),
    }
    if exports:
        payload["export_fields"] = InvoiceExportFieldsUpdate(**exports)
    return InvoiceSettingsUpdate(**payload)


__all__ = [
    "EXPORT_FIELDS",
    "LABEL_FIELDS",
    "InvoiceChanges",
    "SettingsChanges",
    "build_invoice_update",
    "build_settings_update",
    "check_export_fields",
    "parse_labels",
]
