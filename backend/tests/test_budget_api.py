"""Tester for budsjett-endepunktene (planlagt beløp + forbruk/prognose)."""

from datetime import date

from fastapi.testclient import TestClient

from app.db import get_db
from app.db.models import Account, Category
from app.main import app
from app.routes.budget import _days_elapsed, _next_month
from app.sync.transactions import BankTransaction, ingest_transactions


def test_days_elapsed_denne_maneden_bruker_dagens_dato():
    assert _days_elapsed(date(2026, 8, 1), date(2026, 8, 8)) == 8


def test_days_elapsed_tidligere_maned_er_fullt_elapsed():
    assert _days_elapsed(date(2026, 7, 1), date(2026, 8, 8)) == 31


def test_days_elapsed_fremtidig_maned_er_null():
    assert _days_elapsed(date(2026, 9, 1), date(2026, 8, 8)) == 0


def test_next_month_wraps_arstall():
    assert _next_month(date(2026, 12, 1)) == date(2027, 1, 1)
    assert _next_month(date(2026, 5, 1)) == date(2026, 6, 1)


def test_budget_status_beregner_forbruk_fra_kategoriserte_transaksjoner(db):
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    try:
        account = Account(bank_name="DNB", account_number="123", currency="NOK", enablebanking_account_uid="uid-b1")
        db.add(account)
        db.commit()
        db.refresh(account)

        ingest_transactions(
            db,
            account,
            [BankTransaction(bank_tx_id="b-1", date=date(2026, 8, 5), description="REMA 1000", amount=-400)],
        )
        category = db.query(Category).filter_by(name="Dagligvare").one()

        put_response = client.put(
            "/budget-lines",
            json={"month": "2026-08-01", "category_id": str(category.id), "planned_amount": 3000},
        )
        assert put_response.status_code == 200

        status_response = client.get("/budget/status", params={"month": "2026-08-01"})
        assert status_response.status_code == 200
        body = status_response.json()
        assert len(body) == 1
        assert body[0]["category_name"] == "Dagligvare"
        assert body[0]["spent_so_far"] == 400.0
        assert body[0]["planned_amount"] == 3000.0
    finally:
        app.dependency_overrides.clear()


def test_budget_lines_avviser_maned_som_ikke_er_forste_i_maneden(db):
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    try:
        category = Category(name="Bolig", parent_id=None)
        db.add(category)
        db.commit()
        db.refresh(category)

        response = client.put(
            "/budget-lines",
            json={"month": "2026-08-15", "category_id": str(category.id), "planned_amount": 1000},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
