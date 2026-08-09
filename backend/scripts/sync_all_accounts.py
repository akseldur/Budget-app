"""Cron-jobb: henter og lagrer nye transaksjoner for alle registrerte kontoer.

Kjøres periodisk (se crontab på produksjonsserveren) i stedet for at brukeren
må trigge /accounts/{id}/sync-transactions manuelt for hver konto. Én kontos
feil (f.eks. utløpt samtykke) stopper ikke synkroniseringen av de andre.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.db.models import Account  # noqa: E402
from app.integrations.enablebanking import get_transactions  # noqa: E402
from app.integrations.errors import parse_upstream_error  # noqa: E402
from app.sync.transactions import ingest_transactions, parse_enablebanking_transaction  # noqa: E402


def sync_account(db, account: Account) -> int:
    response = get_transactions(
        ENABLE_BANKING_APPLICATION_ID, ENABLE_BANKING_PRIVATE_KEY_PATH, account.enablebanking_account_uid
    )
    if response.status_code != 200:
        upstream = parse_upstream_error(response)
        reconnect_hint = " (samtykket kan ha utløpt - koble til på nytt via /auth/enablebanking/start)" if response.status_code in (401, 403) else ""
        print(f"  FEIL ({response.status_code}){reconnect_hint}: {upstream}")
        return 0

    raw_transactions = response.json().get("transactions", [])
    parsed = [parse_enablebanking_transaction(t) for t in raw_transactions]
    created = ingest_transactions(db, account, parsed)
    return len(created)


def main() -> None:
    db = SessionLocal()
    try:
        accounts = db.query(Account).all()
        print(f"Synker {len(accounts)} konto(er)...")
        for account in accounts:
            print(f"- {account.bank_name} {account.account_number}")
            try:
                count = sync_account(db, account)
                print(f"  {count} nye transaksjoner")
            except Exception as e:  # noqa: BLE001 - én kontos feil skal ikke stoppe resten
                print(f"  UVENTET FEIL: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
