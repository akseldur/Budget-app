"""Henting/lagring av transaksjoner fra banken, og redigering av splitter."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH
from app.db import get_db
from app.db.models import Account, Transaction
from app.integrations.enablebanking import get_transactions
from app.integrations.errors import raise_for_enablebanking_error
from app.sync.transactions import ingest_transactions, parse_enablebanking_transaction, replace_splits

router = APIRouter(tags=["transactions"])


class SplitOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID | None
    amount: float

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    date: date
    description: str
    amount: float
    splits: list[SplitOut]

    model_config = {"from_attributes": True}


class SplitIn(BaseModel):
    category_id: uuid.UUID | None
    amount: float


@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db)) -> list[TransactionOut]:
    return list(db.query(Transaction).order_by(Transaction.date.desc()).all())


@router.post("/accounts/{account_id}/sync-transactions")
def sync_transactions(
    account_id: uuid.UUID,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TransactionOut]:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Ukjent konto")

    response = get_transactions(
        ENABLE_BANKING_APPLICATION_ID,
        ENABLE_BANKING_PRIVATE_KEY_PATH,
        account.enablebanking_account_uid,
        date_from=date_from,
        date_to=date_to,
    )
    raise_for_enablebanking_error(response)

    raw_transactions = response.json().get("transactions", [])
    parsed = [parse_enablebanking_transaction(t) for t in raw_transactions]
    return ingest_transactions(db, account, parsed)


@router.put("/transactions/{transaction_id}/splits")
def update_splits(
    transaction_id: uuid.UUID, splits: list[SplitIn], db: Session = Depends(get_db)
) -> TransactionOut:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Ukjent transaksjon")

    try:
        return replace_splits(db, transaction, [(s.category_id, s.amount) for s in splits])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
