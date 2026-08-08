"""Registrerer bankkontoer i databasen basert på data fra Enable Banking."""

from sqlalchemy.orm import Session

from app.db.models import Account


def upsert_account(
    db: Session,
    *,
    enablebanking_account_uid: str,
    bank_name: str,
    account_number: str,
    currency: str,
) -> Account:
    account = db.query(Account).filter_by(enablebanking_account_uid=enablebanking_account_uid).one_or_none()
    if account is None:
        account = Account(
            enablebanking_account_uid=enablebanking_account_uid,
            bank_name=bank_name,
            account_number=account_number,
            currency=currency,
        )
        db.add(account)
    else:
        account.bank_name = bank_name
        account.account_number = account_number
        account.currency = currency

    db.commit()
    db.refresh(account)
    return account
