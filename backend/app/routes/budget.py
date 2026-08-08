"""Budsjettlinjer og hittil-forbruk/prognose per kategori (inkl. underkategorier)."""

import calendar
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.budget.forecast import Status, forecast
from app.db import get_db
from app.db.models import BudgetLine, Category, Transaction, TransactionSplit

router = APIRouter(tags=["budget"])


class BudgetLineIn(BaseModel):
    month: date
    category_id: uuid.UUID
    planned_amount: float


class BudgetLineOut(BaseModel):
    id: uuid.UUID
    month: date
    category_id: uuid.UUID
    planned_amount: float

    model_config = {"from_attributes": True}


class CategoryForecastOut(BaseModel):
    category_id: uuid.UUID
    category_name: str
    spent_so_far: float
    projected: float
    planned_amount: float
    status: Status


def _days_elapsed(month: date, today: date) -> int:
    if (month.year, month.month) == (today.year, today.month):
        return today.day
    if (month.year, month.month) < (today.year, today.month):
        return calendar.monthrange(month.year, month.month)[1]
    return 0


def _next_month(month: date) -> date:
    if month.month == 12:
        return date(month.year + 1, 1, 1)
    return date(month.year, month.month + 1, 1)


@router.put("/budget-lines")
def upsert_budget_line(body: BudgetLineIn, db: Session = Depends(get_db)) -> BudgetLineOut:
    if body.month.day != 1:
        raise HTTPException(status_code=422, detail="month må være den første i måneden")

    category = db.get(Category, body.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Ukjent kategori")

    line = db.query(BudgetLine).filter_by(month=body.month, category_id=body.category_id).one_or_none()
    if line is None:
        line = BudgetLine(month=body.month, category_id=body.category_id, planned_amount=body.planned_amount)
        db.add(line)
    else:
        line.planned_amount = body.planned_amount

    db.commit()
    db.refresh(line)
    return line


@router.get("/budget/status")
def budget_status(month: date, db: Session = Depends(get_db)) -> list[CategoryForecastOut]:
    if month.day != 1:
        raise HTTPException(status_code=422, detail="month må være den første i måneden")

    days_in_month = calendar.monthrange(month.year, month.month)[1]
    days_elapsed = _days_elapsed(month, date.today())
    next_month = _next_month(month)

    results = []
    for line in db.query(BudgetLine).filter_by(month=month).all():
        category = db.get(Category, line.category_id)
        category_ids = [category.id, *[c.id for c in category.children]]

        spent = (
            db.query(func.coalesce(func.sum(func.abs(TransactionSplit.amount)), 0))
            .join(Transaction, Transaction.id == TransactionSplit.transaction_id)
            .filter(
                TransactionSplit.category_id.in_(category_ids),
                Transaction.date >= month,
                Transaction.date < next_month,
            )
            .scalar()
        )

        result = forecast(
            spent_so_far=float(spent),
            planned_amount=float(line.planned_amount),
            days_elapsed=days_elapsed,
            days_in_month=days_in_month,
        )
        results.append(
            CategoryForecastOut(
                category_id=category.id,
                category_name=category.name,
                spent_so_far=result.spent_so_far,
                projected=result.projected,
                planned_amount=result.planned_amount,
                status=result.status,
            )
        )

    return results
