"""Engangsscript: hent saldo og transaksjoner for en konto fra en aktiv sesjon.

Kjør fra backend/ etter å ha fullført samtykke-flyten (se /auth/enablebanking/callback):
    python scripts/test_enablebanking_accounts.py <account_uid> [date_from] [date_to]

account_uid finnes i "uid"-feltet på kontoen i callback-responsen.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.integrations.enablebanking import get_balances, get_transactions  # noqa: E402

load_dotenv()

account_uid = sys.argv[1]
date_from = sys.argv[2] if len(sys.argv) > 2 else None
date_to = sys.argv[3] if len(sys.argv) > 3 else None

application_id = os.environ["ENABLE_BANKING_APPLICATION_ID"]
private_key_path = os.environ["ENABLE_BANKING_PRIVATE_KEY_PATH"]

print("--- balances ---")
r = get_balances(application_id, private_key_path, account_uid)
print(r.status_code)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))

print("--- transactions ---")
r = get_transactions(application_id, private_key_path, account_uid, date_from=date_from, date_to=date_to)
print(r.status_code)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
