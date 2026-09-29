from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Iterator

    from clockify._pagination import Page


@dataclass(frozen=True, slots=True)
class ListOptions:
    limit: int | None = None
    page: int | None = None
    page_size: int | None = None


def collect[T](
    fetch_all: Callable[[], Iterator[T]],
    fetch_page: Callable[..., Page[T]],
    options: ListOptions,
) -> Iterable[T]:
    if options.page is not None or options.page_size is not None:
        if options.limit is not None:
            message = "--limit cannot be combined with --page/--page-size."
            raise CliError(message, exit_code=ExitCode.USAGE)
        return _paginated(fetch_page, options)
    if options.limit is None:
        return fetch_all()
    return itertools.islice(fetch_all(), options.limit)


def _paginated[T](
    fetch_page: Callable[..., Page[T]],
    options: ListOptions,
) -> Iterable[T]:
    page = options.page if options.page is not None else 1
    return fetch_page(page=page, page_size=options.page_size).items


def list_from_options[T](
    fetch_all: Callable[[], Iterator[T]],
    fetch_page: Callable[..., Page[T]],
    limit: int | None,
    page: int | None,
    page_size: int | None,
) -> Iterable[T]:
    return collect(fetch_all, fetch_page, ListOptions(limit=limit, page=page, page_size=page_size))


__all__ = ["ListOptions", "collect", "list_from_options"]
