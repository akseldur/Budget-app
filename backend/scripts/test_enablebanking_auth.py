"""Engangsscript: bekreft at applikasjonen kan autentisere seg mot Enable Banking.

Kjør fra backend/: python scripts/test_enablebanking_auth.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.integrations.enablebanking import get_application_status  # noqa: E402

load_dotenv()

application_id = os.environ["ENABLE_BANKING_APPLICATION_ID"]
private_key_path = os.environ["ENABLE_BANKING_PRIVATE_KEY_PATH"]

response = get_application_status(application_id, private_key_path)

print(f"Status: {response.status_code}")
print(response.text)
