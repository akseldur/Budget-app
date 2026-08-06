from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.funds import router as funds_router

app = FastAPI(title="Budsjett-app API")
app.include_router(auth_router)
app.include_router(funds_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
