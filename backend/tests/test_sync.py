"""Tester for lagring/kategorisering av transaksjoner (app/sync/transactions.py)."""

from datetime import date

import pytest

from app.db.models import Account, Category
from app.sync.transactions import (
    BankTransaction,
    ingest_transactions,
    parse_enablebanking_transaction,
    replace_splits,
)


def _make_account(db, uid: str = "test-uid-1") -> Account:
    account = Account(
        bank_name="DNB",
        account_number="12345678903",
        currency="NOK",
        enablebanking_account_uid=uid,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_ingest_lagrer_ny_transaksjon_og_kategoriserer_automatisk(db):
    account = _make_account(db)
    tx = BankTransaction(bank_tx_id="tx-1", date=date(2026, 8, 5), description="REMA 1000 OSLO", amount=-249.5)

    created = ingest_transactions(db, account, [tx])

    assert len(created) == 1
    saved = created[0]
    assert float(saved.amount) == -249.5
    assert len(saved.splits) == 1
    split = saved.splits[0]
    assert float(split.amount) == -249.5
    category = db.get(Category, split.category_id)
    assert category.name == "Dagligvare"
    assert category.parent.name == "Mat"


def test_ingest_dedupliserer_pa_bank_tx_id(db):
    account = _make_account(db, uid="test-uid-2")
    tx = BankTransaction(bank_tx_id="tx-2", date=date(2026, 8, 5), description="UKJENT BUTIKK", amount=-100)

    first = ingest_transactions(db, account, [tx])
    second = ingest_transactions(db, account, [tx])

    assert len(first) == 1
    assert len(second) == 0


def test_ingest_ukjent_beskrivelse_blir_ukategorisert(db):
    account = _make_account(db, uid="test-uid-3")
    tx = BankTransaction(bank_tx_id="tx-3", date=date(2026, 8, 5), description="HELT UKJENT XYZ", amount=-50)

    created = ingest_transactions(db, account, [tx])

    assert created[0].splits[0].category_id is None


def test_parse_enablebanking_transaction_debet_blir_negativ():
    raw = {
        "entry_reference": "eb-1",
        "booking_date": "2026-08-05",
        "transaction_amount": {"amount": "249.50", "currency": "NOK"},
        "credit_debit_indicator": "DBIT",
        "remittance_information_unstructured": "REMA 1000 OSLO",
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.amount == -249.5
    assert parsed.bank_tx_id == "eb-1"
    assert parsed.date == date(2026, 8, 5)


def test_parse_enablebanking_transaction_kredit_blir_positiv():
    raw = {
        "entry_reference": "eb-2",
        "value_date": "2026-08-01",
        "transaction_amount": {"amount": "35000", "currency": "NOK"},
        "credit_debit_indicator": "CRDT",
        "remittance_information_unstructured": "LØNN AKER SOLUTIONS",
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.amount == 35000
    assert parsed.date == date(2026, 8, 1)


def test_replace_splits_krever_at_summen_stemmer(db):
    account = _make_account(db, uid="test-uid-4")
    tx = BankTransaction(bank_tx_id="tx-4", date=date(2026, 8, 5), description="UKJENT", amount=-300)
    transaction = ingest_transactions(db, account, [tx])[0]

    with pytest.raises(ValueError):
        replace_splits(db, transaction, [(None, -100)])


def test_replace_splits_godtar_riktig_sum(db):
    account = _make_account(db, uid="test-uid-5")
    tx = BankTransaction(bank_tx_id="tx-5", date=date(2026, 8, 5), description="UKJENT", amount=-300)
    transaction = ingest_transactions(db, account, [tx])[0]

    updated = replace_splits(db, transaction, [(None, -200), (None, -100)])

    assert len(updated.splits) == 2
