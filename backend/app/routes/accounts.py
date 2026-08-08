"""Registrering av bankkontoer og henting av kontoliste.

/accounts/{uid}/details returnerer verken banknavn eller alltid en IBAN (verifisert
mot Mock ASPSP-sandbox 2026-08-08) - banknavnet må derfor komme fra kalleren, som
allerede har det fra "aspsp"-feltet i sesjonen returnert av /auth/enablebanking/callback.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH
from app.db import get_db
from app.db.models import Account
from app.integrations.enablebanking import get_account_details, get_balances
from app.integrations.errors import raise_for_enablebanking_error
from app.sync.accounts import upsert_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountOut(BaseModel):
    id: uuid.UUID
    bank_name: str
    account_number: str
    currency: str
    enablebanking_account_uid: str

    model_config = {"from_attributes": True}


class RegisterAccountRequest(BaseModel):
    enablebanking_account_uid: str
    bank_name: str


class BalanceOut(BaseModel):
    amount: float
    currency: str
    balance_type: str


@router.get("")
def list_accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    return list(db.query(Account).order_by(Account.bank_name).all())


@router.get("/{account_id}/balance")
def get_account_balance(account_id: uuid.UUID, db: Session = Depends(get_db)) -> BalanceOut:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Ukjent konto")

    response = get_balances(ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH, account.enablebanking_account_uid)
    raise_for_enablebanking_error(response)

    balances = response.json().get("balances", [])
    if not balances:
        raise HTTPException(status_code=404, detail="Ingen saldo tilgjengelig for kontoen")

    # "ITAV" (interim available) er nærmest "penger du faktisk har nå" - foretrekk
    # den om den finnes, ellers første oppgitte saldo (verifisert responsform mot
    # Mock ASPSP-sandbox 2026-08-08).
    chosen = next((b for b in balances if b.get("balance_type") == "ITAV"), balances[0])
    amount_block = chosen["balance_amount"]
    return BalanceOut(
        amount=float(amount_block["amount"]),
        currency=amount_block["currency"],
        balance_type=chosen.get("balance_type", ""),
    )


@router.post("/register")
def register_account(body: RegisterAccountRequest, db: Session = Depends(get_db)) -> AccountOut:
    response = get_account_details(
        ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH, body.enablebanking_account_uid
    )
    raise_for_enablebanking_error(response)

    details = response.json()
    return upsert_account(
        db,
        enablebanking_account_uid=body.enablebanking_account_uid,
        bank_name=body.bank_name,
        account_number=(details.get("account_id") or {}).get("iban") or "",
        currency=details.get("currency") or "",
    )
