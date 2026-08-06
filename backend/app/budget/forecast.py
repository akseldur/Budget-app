"""Lineær fremskrivning av forbruk mot budsjett, per kategori.

Ren logikk, ingen databaseavhengighet: tar hittil-forbruk og hvor langt inn
i måneden vi er, og sier om vi ligger an til å holde budsjettet.
"""

from dataclasses import dataclass
from typing import Literal

Status = Literal["green", "yellow", "red"]

YELLOW_THRESHOLD = 0.8  # >= 80 % av budsjett -> gul


@dataclass(frozen=True)
class ForecastResult:
    spent_so_far: float
    projected: float
    planned_amount: float
    status: Status


def forecast(
    spent_so_far: float,
    planned_amount: float,
    days_elapsed: int,
    days_in_month: int,
) -> ForecastResult:
    if days_elapsed <= 0:
        # Ingen dager å fremskrive fra ennå (starten av måneden) - for tidlig å varsle.
        projected = spent_so_far
    else:
        projected = spent_so_far * (days_in_month / days_elapsed)

    if planned_amount <= 0:
        status: Status = "red" if spent_so_far > 0 else "green"
    elif projected > planned_amount:
        status = "red"
    elif projected >= planned_amount * YELLOW_THRESHOLD:
        status = "yellow"
    else:
        status = "green"

    return ForecastResult(
        spent_so_far=spent_so_far,
        projected=projected,
        planned_amount=planned_amount,
        status=status,
    )
