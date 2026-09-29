from __future__ import annotations

from typing import Final

import pytest

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.resolve import Candidate
from clockify_unofficial_cli.services.resolve import resolve

ID_A: Final = "aaaaaaaaaaaaaaaaaaaaaaaa"
ID_B: Final = "bbbbbbbbbbbbbbbbbbbbbbbb"
ID_C: Final = "cccccccccccccccccccccccc"


def test_id_is_taken_without_lookup() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="alpha"), Candidate(id=ID_B, name="beta")]
    # Act
    resolved = resolve(ID_C, candidates, noun="project")
    # Assert
    assert resolved == ID_C


def test_exact_name_match_returns_id() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="alpha"), Candidate(id=ID_B, name="beta")]
    # Act
    resolved = resolve("alpha", candidates, noun="project")
    # Assert
    assert resolved == ID_A


def test_case_insensitive_name_match() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="Alpha Team")]
    # Act
    resolved = resolve("ALPHA team", candidates, noun="project")
    # Assert
    assert resolved == ID_A


def test_unknown_name_raises_not_found() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="alpha")]
    # Act
    with pytest.raises(CliError) as caught:
        resolve("gamma", candidates, noun="client")
    # Assert
    assert caught.value.exit_code == ExitCode.NOT_FOUND
    assert "Unknown client 'gamma'." in caught.value.message


def test_ambiguous_name_raises_usage_with_candidate_ids() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="alpha"), Candidate(id=ID_B, name="alpha")]
    # Act
    with pytest.raises(CliError) as caught:
        resolve("alpha", candidates, noun="tag")
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
    assert ID_A in caught.value.message
    assert ID_B in caught.value.message


def test_partial_name_does_not_match() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="Alpha Team")]
    # Act
    with pytest.raises(CliError) as caught:
        resolve("alpha", candidates, noun="project")
    # Assert
    assert caught.value.exit_code == ExitCode.NOT_FOUND


def test_24_char_non_hex_is_treated_as_name() -> None:
    # Arrange
    candidates = [Candidate(id=ID_A, name="z" * 24)]
    # Act
    resolved = resolve("Z" * 24, candidates, noun="project")
    # Assert
    assert resolved == ID_A
