"""Felles feilhåndtering for Enable Banking-kall i route-laget.

401/403 fra Enable Banking (verifisert responsform: {"code", "message", "error",
"detail"}, se scripts/test_enablebanking_accounts.py) betyr typisk at samtykket
er utløpt eller trukket tilbake - brukeren bør da kobles til banken på nytt via
/auth/enablebanking/start, ikke bare se en generisk feilmelding.
"""

import httpx
from fastapi import HTTPException


def parse_upstream_error(response: httpx.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {"message": response.text}


def raise_for_enablebanking_error(response: httpx.Response) -> None:
    """Bruk for kall som forutsetter et eksisterende samtykke (transaksjoner, saldo,
    kontodetaljer) - IKKE for /auth/enablebanking/start eller /callback selv, der en
    401/403 ikke betyr "koble til på nytt" (det er jo akkurat det brukeren gjør)."""
    if response.status_code == 200:
        return

    upstream = parse_upstream_error(response)

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=409,
            detail={
                "reconnect_required": True,
                "message": "Samtykket til banken er utløpt eller trukket tilbake. Koble til på nytt via /auth/enablebanking/start.",
                "upstream": upstream,
            },
        )

    raise HTTPException(
        status_code=502,
        detail={"reconnect_required": False, "upstream": upstream},
    )
