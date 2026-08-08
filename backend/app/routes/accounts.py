"""Registrering av bankkontoer og henting av kontoliste.

/accounts/{uid}/details returnerer verken banknavn eller alltid en IBAN (verifisert
mot Mock ASPSP-sandbox 2026-08-08) - banknavnet må derfor komme fra kalleren, som
allerede har det fra "aspsp"-feltet i sesjonen returnert av /auth/enablebanking/callback.
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH
from app.db import get_db
from app.db.models import Account
from app.integrations.enablebanking import get_account_details
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


@router.get("")
def list_accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    return list(db.query(Account).order_by(Account.bank_name).all())


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
