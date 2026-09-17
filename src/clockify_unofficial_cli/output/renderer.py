from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence
    from typing import TextIO

    from rich.console import Console

type Record = Mapping[str, object]  # pylint: disable=app-module-const-naming


@dataclass(frozen=True, slots=True)
class Column:
    key: str
    header: str

    # Keys may be dotted paths into nested API objects, e.g. "timeInterval.duration".
    def value(self, record: Record) -> object:
        current: object = record
        for part in self.key.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
        return current


@dataclass(frozen=True, slots=True)
class Dataset:
    records: Sequence[Record]
    columns: Sequence[Column]
    single: bool = False


@dataclass(frozen=True, slots=True)
class RenderTarget:
    console: Console
    stream: TextIO = field(repr=False)


class Renderer(Protocol):
    def render(self, dataset: Dataset) -> None: ...


# JSON output keeps Clockify's camelCase field names so it lines up with the API docs.
def to_record(item: BaseModel | Record) -> Record:
    if isinstance(item, BaseModel):
        return item.model_dump(mode="json", by_alias=True)
    return item


def many(items: Iterable[BaseModel | Record], columns: Sequence[Column]) -> Dataset:
    return Dataset(records=[to_record(item) for item in items], columns=columns)


def single(item: BaseModel | Record, columns: Sequence[Column]) -> Dataset:
    return Dataset(records=[to_record(item)], columns=columns, single=True)
