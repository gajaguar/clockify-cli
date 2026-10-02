from __future__ import annotations

from decimal import ROUND_HALF_UP
from decimal import Decimal
from typing import Final

_CENTS: Final = Decimal(100)


# Clockify stores money as an integer count of the currency's minor unit; people type 120.50.
def to_minor_units(amount: float) -> int:
    return int((Decimal(str(amount)) * _CENTS).to_integral_value(rounding=ROUND_HALF_UP))


__all__ = ["to_minor_units"]
