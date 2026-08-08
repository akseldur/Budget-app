"""DNB/Enable Banking samtykke-flyt (AIS consent).

Start -> redirect til banken -> callback med code -> bytt til session.
`state` lagres midlertidig i minnet for CSRF-validering; god nok for en
enkeltbruker-app i utviklingsfasen, ikke ment å overleve en restart.
"""

import time
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import (
    ENABLE_BANKING_APPLICATION_ID,
    ENABLE_BANKING_PRIVATE_KEY_PATH,
    ENABLE_BANKING_REDIRECT_URL,
)
from app.db import get_db
from app.integrations.enablebanking import exchange_code_for_session, start_authorization
from app.routes.accounts import AccountOut
from app.sync.accounts import upsert_account

router = APIRouter(prefix="/auth/enablebanking", tags=["enablebanking"])

_STATE_TTL_SECONDS = 900
_pending_states: dict[str, float] = {}

ASPSP_NAME = "Mock ASPSP"
ASPSP_COUNTRY = "NO"


def _purge_expired_states() -> None:
    now = time.monotonic()
    expired = [s for s, created in _pending_states.items() if now - created > _STATE_TTL_SECONDS]
    for s in expired:
        del _pending_states[s]


@router.get("/start")
def start() -> RedirectResponse:
    _purge_expired_states()
    state = str(uuid.uuid4())
    _pending_states[state] = time.monotonic()

    valid_until = (datetime.now(UTC) + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = start_authorization(
        ENABLE_BANKING_APPLICATION_ID,
        ENABLE_BANKING_PRIVATE_KEY_PATH,
        aspsp_name=ASPSP_NAME,
        aspsp_country=ASPSP_COUNTRY,
        redirect_url=ENABLE_BANKING_REDIRECT_URL,
        state=state,
        valid_until=valid_until,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=response.text)

    return RedirectResponse(response.json()["url"])


@router.get("/callback")
def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if error:
        raise HTTPException(status_code=400, detail=f"{error}: {error_description}")

    if not state or state not in _pending_states:
        raise HTTPException(status_code=400, detail="Ukjent eller utløpt state")
    del _pending_states[state]

    if not code:
        raise HTTPException(status_code=400, detail="Mangler code i callback")

    response = exchange_code_for_session(
        ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH, code
    )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=response.text)

    session = response.json()
    bank_name = (session.get("aspsp") or {}).get("name") or ASPSP_NAME

    # Sesjonen inneholder allerede full kontoinfo (uid, currency, evt. account_id/iban)
    # for hver konto samtykket til - ingen egen /accounts/{uid}/details-runde nødvendig her.
    registered_accounts = [
        AccountOut.model_validate(
            upsert_account(
                db,
                enablebanking_account_uid=account["uid"],
                bank_name=bank_name,
                account_number=(account.get("account_id") or {}).get("iban") or "",
                currency=account.get("currency") or "",
            )
        )
        for account in session.get("accounts", [])
    ]

    return {"session_id": session.get("session_id"), "accounts": registered_accounts}
