"""Henter live fondskurs fra Yahoo Finance sitt offentlige (nøkkelfrie) chart-API."""

from dataclasses import dataclass

import httpx

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

DNB_TEKNOLOGI_A_SYMBOL = "0P00000MVB.IR"


@dataclass(frozen=True)
class FundPrice:
    symbol: str
    name: str
    price: float
    currency: str


def get_fund_price(symbol: str) -> FundPrice:
    response = httpx.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()
    meta = response.json()["chart"]["result"][0]["meta"]

    return FundPrice(
        symbol=meta["symbol"],
        name=meta["longName"],
        price=meta["regularMarketPrice"],
        currency=meta["currency"],
    )
