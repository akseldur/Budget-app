"""Enkel API-nøkkel-autentisering for egne endepunkter.

Ikke ekte multi-bruker-auth - dette er en enkeltbruker-app. Målet er å unngå
at endepunktene står helt åpne når appen etter hvert eksponeres utover
localhost (jf. Fase 7 i prosjektplanen).
"""

from fastapi import Header, HTTPException

from app.config import APP_API_KEY


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != APP_API_KEY:
        raise HTTPException(status_code=401, detail="Ugyldig eller manglende API-nøkkel")
