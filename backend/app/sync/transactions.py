"""Lagrer transaksjoner hentet fra banken og kategoriserer dem automatisk.

Feltnavnene i parse_enablebanking_transaction() er verifisert mot både Mock
ASPSP i sandbox og ekte DNB i production (2026-08-08). De to avviker på ett
punkt: Mock ASPSP fyller ut entry_reference og creditor/debtor.name, mens ekte
DNB har disse som null og bruker transaction_id + remittance_information i
stedet - derfor prøves begge par.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as date_

from sqlalchemy.orm import Session

from app.categorization.engine import CategoryMatch, categorize
from app.db.models import Account, Category, Transaction, TransactionSplit


@dataclass(frozen=True)
class BankTransaction:
    bank_tx_id: str
    date: date_
    description: str
    amount: float  # positivt = inntekt, negativt = utgift


def parse_enablebanking_transaction(raw: dict) -> BankTransaction:
    amount = abs(float(raw["transaction_amount"]["amount"]))
    is_debit = raw.get("credit_debit_indicator") == "DBIT"
    if is_debit:
        amount = -amount

    booking_date = raw.get("booking_date") or raw["value_date"]

    # Motpartens navn (hvem pengene gikk til/kom fra) er en langt bedre kilde til
    # beskrivelse for regelmotoren enn remittance_information, som i praksis kan
    # være en fritekst-referanse uten butikknavn.
    counterparty = raw.get("creditor") if is_debit else raw.get("debtor")
    counterparty_name = (counterparty or {}).get("name")
    remittance_text = " ".join(line for line in (raw.get("remittance_information") or []) if line)
    description = counterparty_name or remittance_text or "(uten beskrivelse)"

    # entry_reference (Mock ASPSP) og transaction_id (ekte DNB) er aldri begge
    # utfylt samtidig i det vi har sett - bruk den som faktisk finnes.
    bank_tx_id = raw.get("entry_reference") or raw.get("transaction_id")
    if not bank_tx_id:
        raise ValueError(f"Transaksjon mangler både entry_reference og transaction_id: {raw!r}")

    return BankTransaction(
        bank_tx_id=bank_tx_id,
        date=date_.fromisoformat(booking_date),
        description=description,
        amount=amount,
    )


def _find_or_create_category(db: Session, match: CategoryMatch) -> Category:
    parent = db.query(Category).filter_by(name=match.parent, parent_id=None).one_or_none()
    if parent is None:
        parent = Category(name=match.parent, parent_id=None)
        db.add(parent)
        db.flush()

    child = db.query(Category).filter_by(name=match.child, parent_id=parent.id).one_or_none()
    if child is None:
        child = Category(name=match.child, parent_id=parent.id)
        db.add(child)
        db.flush()

    return child


def ingest_transactions(db: Session, account: Account, transactions: Iterable[BankTransaction]) -> list[Transaction]:
    """Lagrer nye transaksjoner for kontoen; hopper stille over de som finnes fra før.

    Hver ny transaksjon får automatisk én transaction_split med hele beløpet,
    kategorisert via regelmotoren (eller ukategorisert hvis ingen regel treffer).
    Splitting til flere kategorier skjer i etterkant via PUT /transactions/{id}/splits.
    """
    transactions = list(transactions)
    incoming_ids = {t.bank_tx_id for t in transactions}
    existing_ids = {
        row.bank_tx_id for row in db.query(Transaction.bank_tx_id).filter(Transaction.bank_tx_id.in_(incoming_ids))
    }

    created: list[Transaction] = []
    for t in transactions:
        if t.bank_tx_id in existing_ids:
            continue

        match = categorize(t.description)
        category = _find_or_create_category(db, match) if match else None

        transaction = Transaction(
            account_id=account.id,
            bank_tx_id=t.bank_tx_id,
            date=t.date,
            description=t.description,
            amount=t.amount,
            splits=[TransactionSplit(category_id=category.id if category else None, amount=t.amount)],
        )
        db.add(transaction)
        created.append(transaction)

    db.commit()
    return created


def create_manual_transaction(
    db: Session,
    account: Account,
    *,
    date: date_,
    description: str,
    amount: float,
    category_id: uuid.UUID | None,
) -> Transaction:
    """Manuell registrering (skjerm "Ny transaksjon") - ikke hentet fra banken.

    bank_tx_id må være unik og non-null i skjemaet; genererer en syntetisk en
    siden manuelle transaksjoner ikke har noen ekte bank-referanse.
    """
    transaction = Transaction(
        account_id=account.id,
        bank_tx_id=f"manual-{uuid.uuid4()}",
        date=date,
        description=description,
        amount=amount,
        splits=[TransactionSplit(category_id=category_id, amount=amount)],
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def replace_splits(
    db: Session, transaction: Transaction, splits: list[tuple[uuid.UUID | None, float]]
) -> Transaction:
    """Erstatter en transaksjons splitter. Summen må alltid være lik transaksjonsbeløpet."""
    total = sum(amount for _, amount in splits)
    if abs(total - float(transaction.amount)) > 0.005:
        raise ValueError(f"Summen av splitter ({total}) må være lik transaksjonsbeløpet ({transaction.amount})")

    transaction.splits = [TransactionSplit(category_id=category_id, amount=amount) for category_id, amount in splits]
    db.commit()
    db.refresh(transaction)
    return transaction
