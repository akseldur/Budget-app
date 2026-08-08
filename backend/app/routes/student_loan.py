"""Manuell registrering av studielånssaldo.

Lånekassen tilbyr ikke noe API for enkeltpersoner (DSOP-API er kun for
finansinstitusjoner) - saldoen registreres derfor manuelt med jevne mellomrom.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import StudentLoanSnapshot

router = APIRouter(prefix="/student-loan-snapshots", tags=["student-loan"])


class SnapshotIn(BaseModel):
    balance: float
    as_of_date: date


class SnapshotOut(BaseModel):
    id: uuid.UUID
    balance: float
    as_of_date: date

    model_config = {"from_attributes": True}


@router.post("")
def create_snapshot(body: SnapshotIn, db: Session = Depends(get_db)) -> SnapshotOut:
    snapshot = StudentLoanSnapshot(balance=body.balance, as_of_date=body.as_of_date)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("")
def list_snapshots(db: Session = Depends(get_db)) -> list[SnapshotOut]:
    return list(db.query(StudentLoanSnapshot).order_by(StudentLoanSnapshot.as_of_date.desc()).all())


@router.get("/latest")
def latest_snapshot(db: Session = Depends(get_db)) -> SnapshotOut:
    snapshot = db.query(StudentLoanSnapshot).order_by(StudentLoanSnapshot.as_of_date.desc()).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Ingen studielånssaldo registrert ennå")
    return snapshot
