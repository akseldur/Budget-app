"""Henting av kategoritreet (opprettes i dag lazy av regelmotoren ved første treff)."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Category

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}


@router.get("")
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    return list(db.query(Category).order_by(Category.name).all())
