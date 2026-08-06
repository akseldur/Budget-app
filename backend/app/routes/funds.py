from fastapi import APIRouter

from app.integrations.fund_price import DNB_TEKNOLOGI_A_SYMBOL, FundPrice, get_fund_price

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/dnb-teknologi-a")
def dnb_teknologi_a() -> FundPrice:
    return get_fund_price(DNB_TEKNOLOGI_A_SYMBOL)
