from fastapi import FastAPI

from app.routes.accounts import router as accounts_router
from app.routes.auth import router as auth_router
from app.routes.budget import router as budget_router
from app.routes.funds import router as funds_router
from app.routes.student_loan import router as student_loan_router
from app.routes.transactions import router as transactions_router

app = FastAPI(title="Budsjett-app API")
app.include_router(auth_router)
app.include_router(funds_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(budget_router)
app.include_router(student_loan_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
