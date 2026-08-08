"""Tester for at API-nøkkel-sjekken faktisk håndhever seg selv (uten override)."""

from fastapi.testclient import TestClient

from app.config import APP_API_KEY
from app.db import get_db
from app.main import app


def test_beskyttet_endepunkt_avviser_uten_nokkel(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/accounts")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_beskyttet_endepunkt_avviser_feil_nokkel(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/accounts", headers={"X-API-Key": "feil-nokkel"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_beskyttet_endepunkt_godtar_riktig_nokkel(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/accounts", headers={"X-API-Key": APP_API_KEY})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_helsesjekk_krever_ikke_nokkel():
    client = TestClient(app)
    assert client.get("/health").status_code == 200


def test_bank_redirect_endepunkt_krever_ikke_nokkel():
    client = TestClient(app, follow_redirects=False)
    response = client.get("/auth/enablebanking/callback", params={"state": "ukjent"})
    assert response.status_code != 401
