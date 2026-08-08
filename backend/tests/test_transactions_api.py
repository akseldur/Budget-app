"""Tester for GET /transactions/{id}."""

from datetime import date

from fastapi.testclient import TestClient

from app.db import get_db
from app.db.models import Account
from app.main import app
from app.security import require_api_key
from app.sync.transactions import BankTransaction, ingest_transactions


def _client(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_api_key] = lambda: None
    return TestClient(app)


def test_hent_enkelt_transaksjon(db):
    account = Account(bank_name="DNB", account_number="123", currency="NOK", enablebanking_account_uid="uid-t1")
    db.add(account)
    db.commit()
    db.refresh(account)

    transaction = ingest_transactions(
        db, account, [BankTransaction(bank_tx_id="tx-single", date=date(2026, 8, 5), description="Test", amount=-99)]
    )[0]

    try:
        response = _client(db).get(f"/transactions/{transaction.id}")
        assert response.status_code == 200
        assert response.json()["description"] == "Test"
    finally:
        app.dependency_overrides.clear()


def test_hent_ukjent_transaksjon_gir_404(db):
    try:
        response = _client(db).get("/transactions/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_opprett_manuell_transaksjon(db):
    account = Account(bank_name="DNB", account_number="123", currency="NOK", enablebanking_account_uid="uid-m1")
    db.add(account)
    db.commit()
    db.refresh(account)

    try:
        response = _client(db).post(
            "/transactions",
            json={
                "account_id": str(account.id),
                "date": "2026-08-06",
                "description": "Kontantuttak bursdagsgave",
                "amount": -150,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["description"] == "Kontantuttak bursdagsgave"
        assert body["amount"] == -150.0
        assert body["splits"][0]["category_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_opprett_manuell_transaksjon_ukjent_konto_gir_404(db):
    try:
        response = _client(db).post(
            "/transactions",
            json={
                "account_id": "00000000-0000-0000-0000-000000000000",
                "date": "2026-08-06",
                "description": "Test",
                "amount": -50,
            },
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
