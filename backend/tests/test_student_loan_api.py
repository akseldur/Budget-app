"""Tester for manuell studielån-saldoregistrering."""

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


def _client(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_latest_uten_registrerte_snapshots_gir_404(db):
    client = _client(db)
    try:
        response = client.get("/student-loan-snapshots/latest")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_registrer_og_hent_siste_saldo(db):
    client = _client(db)
    try:
        client.post("/student-loan-snapshots", json={"balance": 150000, "as_of_date": "2026-01-01"})
        client.post("/student-loan-snapshots", json={"balance": 145000, "as_of_date": "2026-07-01"})

        response = client.get("/student-loan-snapshots/latest")
        assert response.status_code == 200
        assert response.json()["balance"] == 145000.0
        assert response.json()["as_of_date"] == "2026-07-01"

        list_response = client.get("/student-loan-snapshots")
        assert len(list_response.json()) == 2
    finally:
        app.dependency_overrides.clear()
