# Budsjett-app

Personlig økonomi-app for automatisk kategorisering av banktransaksjoner (DNB), budsjett med prognose/varsel, og oversikt over fond (DNB Teknologi A) og studielån. Ikke-kommersielt, kun til eget bruk.

## Stack

- Backend: FastAPI (Python)
- Database: PostgreSQL
- Bank-integrasjon: Enable Banking (PSD2, restricted mode)
- Fonddata: Yahoo Finance / Finnhub
- Frontend: SwiftUI eller React Native (iOS)

## Kom i gang (lokalt)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fyll inn egne nøkler, aldri commit .env
docker compose up -d   # starter Postgres
uvicorn app.main:app --reload
```

Helsesjekk: `GET http://localhost:8000/health`

## Struktur

```
backend/
  app/
    main.py        # FastAPI-app, helsesjekk
  requirements.txt
  .env.example
docker-compose.yml
```

Se prosjektplanen (roadmap, databaseskjema, nøkkellogikk) for detaljer om fasene.
