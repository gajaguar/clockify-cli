from __future__ import annotations

import pytest

from clockify_unofficial_cli.services.money import to_minor_units


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(120.5, 12050), (0.1, 10), (0.58, 58), (1.005, 101), (0, 0), (-2.5, -250)],
)
def test_to_minor_units_rounds_half_up_without_float_noise(amount: float, expected: int) -> None:
    # Arrange
    value = amount
    # Act
    result = to_minor_units(value)
    # Assert
    assert result == expected
