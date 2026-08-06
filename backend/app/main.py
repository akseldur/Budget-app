from fastapi import FastAPI

app = FastAPI(title="Budsjett-app API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
