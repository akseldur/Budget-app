"""Henting og manuell oppretting av kategoritreet.

Kategorier opprettes ellers lazy av regelmotoren ved første transaksjonstreff
(se app.sync.transactions) - dette endepunktet lar brukeren opprette en
kategori direkte i appen, uten å vente på en matchende transaksjon.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Category
from app.sync.transactions import get_or_create_category

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    parent_name: str
    name: str


@router.get("")
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    return list(db.query(Category).order_by(Category.name).all())


@router.post("", status_code=201)
def create_category(body: CategoryCreate, db: Session = Depends(get_db)) -> CategoryOut:
    parent_name = body.parent_name.strip()
    name = body.name.strip()
    if not parent_name or not name:
        raise HTTPException(status_code=422, detail="Gruppe og kategorinavn kan ikke være tomme")

    category = get_or_create_category(db, parent_name, name)
    db.commit()
    db.refresh(category)
    return category
