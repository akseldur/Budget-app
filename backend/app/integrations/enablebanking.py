"""Minimal klient mot Enable Banking sitt API (PSD2).

Autentisering skjer med en JWT signert med applikasjonens private RSA-nøkkel,
sendt som Bearer-token. Se https://enablebanking.com/docs/api/reference/.
"""

import time
from pathlib import Path

import httpx
import jwt

API_BASE_URL = "https://api.enablebanking.com"


def build_jwt(application_id: str, private_key_path: str, ttl_seconds: int = 3600) -> str:
    private_key = Path(private_key_path).read_text()
    now = int(time.time())

    return jwt.encode(
        payload={
            "iss": "enablebanking.com",
            "aud": "api.enablebanking.com",
            "iat": now,
            "exp": now + ttl_seconds,
        },
        key=private_key,
        algorithm="RS256",
        headers={"kid": application_id},
    )


def get_application_status(application_id: str, private_key_path: str) -> httpx.Response:
    token = build_jwt(application_id, private_key_path)
    return httpx.get(
        f"{API_BASE_URL}/application",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=15,
    )
