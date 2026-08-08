"""Tester for fondskurs-caching (app/sync/fund_price.py)."""

from datetime import UTC, datetime, timedelta

from app.db.models import FundPriceSnapshot
from app.integrations.fund_price import FundPrice
from app.sync import fund_price as fund_price_sync


def test_henter_live_ved_tom_cache(db, monkeypatch):
    calls = []

    def fake_get_fund_price(symbol):
        calls.append(symbol)
        return FundPrice(symbol=symbol, name="DNB Teknologi A", price=100.0, currency="NOK")

    monkeypatch.setattr(fund_price_sync, "get_fund_price", fake_get_fund_price)

    result = fund_price_sync.get_cached_fund_price(db, "SYM", "DNB Teknologi A", "NOK")

    assert result.price == 100.0
    assert calls == ["SYM"]
    assert db.query(FundPriceSnapshot).count() == 1


def test_bruker_cache_innenfor_ttl(db, monkeypatch):
    db.add(FundPriceSnapshot(fund_isin="SYM", price=200.0, fetched_at=datetime.now(UTC)))
    db.commit()

    def fail_if_called(symbol):
        raise AssertionError("skulle ikke hentet live siden cachen er fersk")

    monkeypatch.setattr(fund_price_sync, "get_fund_price", fail_if_called)

    result = fund_price_sync.get_cached_fund_price(db, "SYM", "DNB Teknologi A", "NOK")

    assert result.price == 200.0


def test_henter_live_pa_nytt_nar_cache_er_utgatt(db, monkeypatch):
    stale_time = datetime.now(UTC) - fund_price_sync.CACHE_TTL - timedelta(minutes=1)
    db.add(FundPriceSnapshot(fund_isin="SYM", price=200.0, fetched_at=stale_time))
    db.commit()

    calls = []

    def fake_get_fund_price(symbol):
        calls.append(symbol)
        return FundPrice(symbol=symbol, name="DNB Teknologi A", price=300.0, currency="NOK")

    monkeypatch.setattr(fund_price_sync, "get_fund_price", fake_get_fund_price)

    result = fund_price_sync.get_cached_fund_price(db, "SYM", "DNB Teknologi A", "NOK")

    assert result.price == 300.0
    assert calls == ["SYM"]
