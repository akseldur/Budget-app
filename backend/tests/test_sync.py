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
    # Faktisk responsform fra Mock ASPSP (sandbox), verifisert 2026-08-08.
    raw = {
        "entry_reference": "1javb",
        "booking_date": "2026-08-05",
        "value_date": "2026-08-03",
        "transaction_amount": {"amount": "9.54", "currency": "EUR"},
        "credit_debit_indicator": "DBIT",
        "creditor": {"name": "REMA 1000 OSLO"},
        "debtor": None,
        "remittance_information": ["REMA 1000 OSLO-DBIT-9.54-1javb"],
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.amount == -9.54
    assert parsed.bank_tx_id == "1javb"
    assert parsed.date == date(2026, 8, 5)
    assert parsed.description == "REMA 1000 OSLO"


def test_parse_enablebanking_transaction_kredit_blir_positiv():
    raw = {
        "entry_reference": "eb-2",
        "value_date": "2026-08-01",
        "transaction_amount": {"amount": "35000", "currency": "NOK"},
        "credit_debit_indicator": "CRDT",
        "creditor": None,
        "debtor": {"name": "AKER SOLUTIONS"},
        "remittance_information": ["LØNN"],
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.amount == 35000
    assert parsed.date == date(2026, 8, 1)
    assert parsed.description == "AKER SOLUTIONS"


def test_parse_enablebanking_transaction_uten_motpartsnavn_faller_tilbake_pa_remittance():
    raw = {
        "entry_reference": "eb-3",
        "booking_date": "2026-08-02",
        "transaction_amount": {"amount": "100", "currency": "NOK"},
        "credit_debit_indicator": "DBIT",
        "creditor": None,
        "remittance_information": ["Faktura 123"],
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.description == "Faktura 123"


def test_parse_enablebanking_transaction_ekte_dnb_uten_entry_reference():
    # Faktisk responsform fra ekte DNB i production/restricted mode, verifisert
    # 2026-08-08: entry_reference og creditor/debtor er null, transaction_id og
    # remittance_information er det som faktisk er utfylt.
    raw = {
        "entry_reference": None,
        "transaction_id": "MDExNl8wMDI5NDQ1NjY4NTIxXzAwMDAwMDE",
        "booking_date": "2026-08-07",
        "value_date": "2026-08-07",
        "transaction_amount": {"currency": "NOK", "amount": "70.43"},
        "credit_debit_indicator": "DBIT",
        "creditor": None,
        "debtor": None,
        "remittance_information": ["Varekjøp, Kl. 11.35 Versjon 1 Aut. 349259, 3142 Kværner St Kjøtteinsveg Stord"],
    }

    parsed = parse_enablebanking_transaction(raw)

    assert parsed.bank_tx_id == "MDExNl8wMDI5NDQ1NjY4NTIxXzAwMDAwMDE"
    assert parsed.amount == -70.43
    assert parsed.description == "Varekjøp, Kl. 11.35 Versjon 1 Aut. 349259, 3142 Kværner St Kjøtteinsveg Stord"


def test_parse_enablebanking_transaction_uten_id_gir_feil():
    raw = {
        "entry_reference": None,
        "transaction_id": None,
        "booking_date": "2026-08-07",
        "transaction_amount": {"currency": "NOK", "amount": "10"},
        "credit_debit_indicator": "DBIT",
        "remittance_information": ["Noe"],
    }

    with pytest.raises(ValueError):
        parse_enablebanking_transaction(raw)


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
