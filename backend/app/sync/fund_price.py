"""Cacher fondskurs i databasen - Yahoo Finance trenger ikke sjekkes på hver request."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import FundPriceSnapshot
from app.integrations.fund_price import FundPrice, get_fund_price

CACHE_TTL = timedelta(minutes=15)


def get_cached_fund_price(db: Session, symbol: str, name: str, currency: str) -> FundPrice:
    latest = (
        db.query(FundPriceSnapshot)
        .filter_by(fund_isin=symbol)
        .order_by(FundPriceSnapshot.fetched_at.desc())
        .first()
    )
    now = datetime.now(UTC)
    if latest is not None and now - latest.fetched_at < CACHE_TTL:
        return FundPrice(symbol=symbol, name=name, price=float(latest.price), currency=currency)

    fresh = get_fund_price(symbol)
    db.add(FundPriceSnapshot(fund_isin=symbol, price=fresh.price, fetched_at=now))
    db.commit()
    return fresh
