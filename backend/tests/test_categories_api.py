"""Tester for GET /categories."""

from fastapi.testclient import TestClient

from app.db import get_db
from app.db.models import Category
from app.main import app
from app.security import require_api_key


def _client(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_api_key] = lambda: None
    return TestClient(app)


def test_lister_kategorier_med_foreldre(db):
    client = _client(db)
    try:
        parent = Category(name="Mat", parent_id=None)
        db.add(parent)
        db.commit()
        db.refresh(parent)
        child = Category(name="Dagligvare", parent_id=parent.id)
        db.add(child)
        db.commit()

        response = client.get("/categories")
        assert response.status_code == 200
        names = {c["name"] for c in response.json()}
        assert names == {"Mat", "Dagligvare"}
    finally:
        app.dependency_overrides.clear()


def test_oppretter_ny_kategori_med_ny_foreldrekategori(db):
    client = _client(db)
    try:
        response = client.post("/categories", json={"parent_name": "Fritid", "name": "Kino"})
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Kino"

        names = {c.name for c in db.query(Category).all()}
        assert names == {"Fritid", "Kino"}
    finally:
        app.dependency_overrides.clear()


def test_oppretter_kategori_gjenbruker_eksisterende_foreldre(db):
    client = _client(db)
    try:
        parent = Category(name="Mat", parent_id=None)
        db.add(parent)
        db.commit()

        response = client.post("/categories", json={"parent_name": "Mat", "name": "Snacks"})
        assert response.status_code == 201

        parents = db.query(Category).filter_by(name="Mat", parent_id=None).all()
        assert len(parents) == 1
    finally:
        app.dependency_overrides.clear()


def test_oppretter_kategori_med_tom_navn_feiler(db):
    client = _client(db)
    try:
        response = client.post("/categories", json={"parent_name": "Mat", "name": "   "})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
