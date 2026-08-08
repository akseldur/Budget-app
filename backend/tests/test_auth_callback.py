"""Tester for at consent-callback auto-registrerer kontoer fra sesjonen.

Kun selve HTTP-kallet mot Enable Banking er erstattet (exchange_code_for_session) -
databasen er ekte, samme som resten av testsuiten.
"""

import time

from fastapi.testclient import TestClient

from app.db import get_db
from app.db.models import Account
from app.main import app
from app.routes import auth as auth_routes


class _FakeSessionResponse:
    status_code = 200

    def __init__(self, body: dict):
        self._body = body

    def json(self) -> dict:
        return self._body


def test_callback_auto_registrerer_kontoer_fra_sesjonen(db, monkeypatch):
    state = "test-state-1"
    auth_routes._pending_states[state] = time.monotonic()

    fake_session = {
        "session_id": "sess-1",
        "accounts": [
            {"uid": "acc-uid-1", "currency": "NOK", "account_id": {"iban": "NO1234567890"}},
        ],
        "aspsp": {"name": "DNB", "country": "NO"},
    }
    monkeypatch.setattr(
        auth_routes, "exchange_code_for_session", lambda *a, **k: _FakeSessionResponse(fake_session)
    )

    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/auth/enablebanking/callback", params={"state": state, "code": "code-1"})

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == "sess-1"
        assert len(body["accounts"]) == 1
        assert body["accounts"][0]["bank_name"] == "DNB"
        assert body["accounts"][0]["account_number"] == "NO1234567890"

        account = db.query(Account).filter_by(enablebanking_account_uid="acc-uid-1").one()
        assert account.currency == "NOK"
    finally:
        app.dependency_overrides.clear()


def test_callback_avviser_ukjent_state(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/auth/enablebanking/callback", params={"state": "ukjent-state", "code": "x"})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
