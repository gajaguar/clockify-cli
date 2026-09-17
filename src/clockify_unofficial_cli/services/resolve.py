from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable

    from clockify import ProjectId

    from clockify_unofficial_cli.runtime.context import AppContext


_HEX_CHARS: Final[frozenset[str]] = frozenset("0123456789abcdef")
_ID_LENGTH: Final = 24


def _looks_like_id(term: str) -> bool:
    return len(term) == _ID_LENGTH and all(character in _HEX_CHARS for character in term.lower())


def _render_candidates(candidates: Iterable[str]) -> str:
    rendered = ", ".join(candidates)
    return f"candidates: {rendered}"


# Pattern shared by every resolve_* helper: pass a term that is already an ID,
# an exact case-insensitive name match, or surface a clear error.
@dataclass(frozen=True, slots=True)
class Candidate:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class _Resolver:
    candidates: list[Candidate]
    noun: str

    def resolve(self, term: str) -> str:
        if _looks_like_id(term):
            return term
        lowered = term.casefold()
        matches = [candidate for candidate in self.candidates if candidate.name.casefold() == lowered]
        if len(matches) == 1:
            return matches[0].id
        if not matches:
            message = f"Unknown {self.noun} '{term}'."
            raise CliError(message, exit_code=ExitCode.NOT_FOUND)
        ids = [candidate.id for candidate in matches]
        message = f"Ambiguous {self.noun} '{term}'; {_render_candidates(ids)}."
        raise CliError(message, exit_code=ExitCode.USAGE)


def _candidate_ids_from(items: Iterable[Any], *, name: Callable[[Any], str]) -> list[Candidate]:
    return [Candidate(id=str(item.id), name=name(item)) for item in items]


def resolve(term: str, candidates: list[Candidate], *, noun: str) -> str:
    return _Resolver(candidates=candidates, noun=noun).resolve(term)


def resolve_client(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.clients.list(), name=lambda item: item.name)
    return resolve(term, candidates, noun="client")


def resolve_project(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.projects.list(), name=lambda item: item.name)
    return resolve(term, candidates, noun="project")


def resolve_tag(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.tags.list(), name=lambda item: item.name)
    return resolve(term, candidates, noun="tag")


def resolve_custom_field(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.custom_fields.list(), name=lambda item: item.name)
    return resolve(term, candidates, noun="custom field")


def resolve_group(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.user_groups.list(), name=lambda item: item.name)
    return resolve(term, candidates, noun="group")


def resolve_task(app_context: AppContext, project_id: ProjectId, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(workspace.tasks.list(project_id), name=lambda item: item.name)
    return resolve(term, candidates, noun="task")


def resolve_user(app_context: AppContext, term: str) -> str:
    workspace = app_context.workspace()
    candidates = _candidate_ids_from(
        workspace.users.list(),
        name=lambda item: item.email or item.name,
    )
    by_name = [
        Candidate(id=str(item.id), name=item.name) for item in workspace.users.list() if item.email != item.name
    ]
    candidates.extend(by_name)
    return resolve(term, candidates, noun="user")


__all__ = [
    "Candidate",
    "resolve",
    "resolve_client",
    "resolve_custom_field",
    "resolve_group",
    "resolve_project",
    "resolve_tag",
    "resolve_task",
    "resolve_user",
]
