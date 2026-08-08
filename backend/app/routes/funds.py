from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.integrations.fund_price import DNB_TEKNOLOGI_A_SYMBOL, FundPrice
from app.sync.fund_price import get_cached_fund_price

router = APIRouter(prefix="/funds", tags=["funds"])

# Navn/valuta endrer seg ikke mellom kursoppdateringer - fund_price_snapshots
# lagrer derfor bare pris+tidspunkt, ikke disse.
DNB_TEKNOLOGI_A_NAME = "DNB Teknologi A"
DNB_TEKNOLOGI_A_CURRENCY = "NOK"


@router.get("/dnb-teknologi-a")
def dnb_teknologi_a(db: Session = Depends(get_db)) -> FundPrice:
    return get_cached_fund_price(db, DNB_TEKNOLOGI_A_SYMBOL, DNB_TEKNOLOGI_A_NAME, DNB_TEKNOLOGI_A_CURRENCY)
