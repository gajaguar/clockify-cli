from __future__ import annotations

import datetime
import mimetypes
from dataclasses import dataclass
from typing import TYPE_CHECKING

from clockify import ExpenseChangeField
from clockify import ExpenseFile
from clockify import ExpenseUpdate

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import Candidate
from clockify_unofficial_cli.services.resolve import resolve

if TYPE_CHECKING:
    from pathlib import Path

    from clockify import Expense
    from clockify import ExpenseCategory

    from clockify_unofficial_cli.runtime.context import AppContext


def read_receipt(path: Path) -> ExpenseFile:
    guessed, _ = mimetypes.guess_type(path.name)
    try:
        content = path.read_bytes()
    except OSError as exc:
        message = f"Cannot read '{path}': {exc.strerror}."
        raise CliError(message, exit_code=ExitCode.USAGE) from exc
    return ExpenseFile(filename=path.name, content=content, content_type=guessed)


# Clockify has no endpoint that reads one category, so the list is the only source for it.
def find_category(app_context: AppContext, term: str) -> ExpenseCategory:
    categories = list(app_context.workspace().expense_categories.list())
    candidates = [Candidate(id=str(category.id), name=category.name or str(category.id)) for category in categories]
    category_id = resolve(term, candidates, noun="expense category")
    for category in categories:
        if str(category.id) == category_id:
            return category
    message = f"Unknown expense category '{term}'."
    raise CliError(message, exit_code=ExitCode.NOT_FOUND)


# Ids are already resolved by the caller; None means the option was not passed.
@dataclass(frozen=True, slots=True)
class ExpenseChanges:
    category_id: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    date: str | None = None
    amount: float | None = None
    billable: bool | None = None
    notes: str | None = None
    receipt: ExpenseFile | None = None

    def fields(self) -> list[ExpenseChangeField]:
        touched = {
            ExpenseChangeField.CATEGORY: self.category_id,
            ExpenseChangeField.PROJECT: self.project_id,
            ExpenseChangeField.TASK: self.task_id,
            ExpenseChangeField.DATE: self.date,
            ExpenseChangeField.AMOUNT: self.amount,
            ExpenseChangeField.BILLABLE: self.billable,
            ExpenseChangeField.NOTES: self.notes,
            ExpenseChangeField.FILE: self.receipt,
        }
        return [field for field, value in touched.items() if value is not None]


# Clockify's PUT lists the fields to change in `changeFields`, but still wants the identifying ones
# (user, category, date, amount), so those are copied from the stored expense when not changed.
def build_update(current: Expense, changes: ExpenseChanges) -> ExpenseUpdate:
    changed = changes.fields()
    if not changed:
        message = "Nothing to update; pass at least one option to change."
        raise CliError(message, exit_code=ExitCode.USAGE)
    stored_date = current.date
    when = changes.date or stored_date
    optional: dict[str, object] = {
        "project_id": changes.project_id or current.project_id,
        "task_id": changes.task_id or current.task_id,
        "billable": changes.billable if changes.billable is not None else current.billable,
        "notes": changes.notes if changes.notes is not None else current.notes,
        "file": changes.receipt,
    }
    return ExpenseUpdate(
        user_id=current.user_id,  # type: ignore[arg-type]
        category_id=changes.category_id or current.category_id,  # type: ignore[arg-type]
        date=parse_instant(when) if when else datetime.datetime.now(datetime.UTC),
        amount=changes.amount if changes.amount is not None else current.total or 0.0,
        change_fields=changed,
        **{key: value for key, value in optional.items() if value is not None},  # type: ignore[arg-type]
    )


__all__ = ["ExpenseChanges", "build_update", "find_category", "read_receipt"]
