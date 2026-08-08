"""Tester for GET /accounts/{id}/balance.

Kun selve HTTP-kallet mot Enable Banking er erstattet (get_balances) - responsformen
matcher det som er verifisert live mot Mock ASPSP-sandbox (2026-08-08).
"""

import httpx
from fastapi.testclient import TestClient

from app.db import get_db
from app.db.models import Account
from app.main import app
from app.routes import accounts as accounts_routes
from app.security import require_api_key


def _client(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_api_key] = lambda: None
    return TestClient(app)


def _make_account(db) -> Account:
    account = Account(bank_name="DNB", account_number="123", currency="NOK", enablebanking_account_uid="uid-bal")
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_balanse_foretrekker_itav_fremfor_andre_typer(db, monkeypatch):
    account = _make_account(db)

    fake_body = {
        "balances": [
            {"balance_type": "CLBD", "balance_amount": {"currency": "NOK", "amount": "100.00"}},
            {"balance_type": "ITAV", "balance_amount": {"currency": "NOK", "amount": "45.73"}},
        ]
    }
    monkeypatch.setattr(
        accounts_routes, "get_balances", lambda *a, **k: httpx.Response(status_code=200, json=fake_body)
    )

    try:
        response = _client(db).get(f"/accounts/{account.id}/balance")
        assert response.status_code == 200
        body = response.json()
        assert body["amount"] == 45.73
        assert body["balance_type"] == "ITAV"
    finally:
        app.dependency_overrides.clear()


def test_balanse_faller_tilbake_pa_forste_hvis_ingen_itav(db, monkeypatch):
    account = _make_account(db)

    fake_body = {"balances": [{"balance_type": "CLBD", "balance_amount": {"currency": "NOK", "amount": "100.00"}}]}
    monkeypatch.setattr(
        accounts_routes, "get_balances", lambda *a, **k: httpx.Response(status_code=200, json=fake_body)
    )

    try:
        response = _client(db).get(f"/accounts/{account.id}/balance")
        assert response.status_code == 200
        assert response.json()["balance_type"] == "CLBD"
    finally:
        app.dependency_overrides.clear()


def test_balanse_ukjent_konto_gir_404(db):
    try:
        response = _client(db).get("/accounts/00000000-0000-0000-0000-000000000000/balance")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
