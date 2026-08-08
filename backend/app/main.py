from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.accounts import router as accounts_router
from app.routes.auth import router as auth_router
from app.routes.budget import router as budget_router
from app.routes.categories import router as categories_router
from app.routes.funds import router as funds_router
from app.routes.student_loan import router as student_loan_router
from app.routes.transactions import router as transactions_router
from app.security import require_api_key

app = FastAPI(title="Budsjett-app API")

# Kun relevant for Expo sin web-target under utvikling (native iOS bruker ikke
# CORS) - begrenset til localhost, ikke "*", siden appen uansett er lokal/enkeltbruker.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

# auth_router er unntatt: /start og /callback nås via nettleser-redirect fra
# banken, som ikke kan sette en custom header. /callback er beskyttet av sin
# egen state/code-CSRF-sjekk i stedet.
app.include_router(auth_router)

_protected = [Depends(require_api_key)]
app.include_router(funds_router, dependencies=_protected)
app.include_router(accounts_router, dependencies=_protected)
app.include_router(transactions_router, dependencies=_protected)
app.include_router(budget_router, dependencies=_protected)
app.include_router(student_loan_router, dependencies=_protected)
app.include_router(categories_router, dependencies=_protected)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
