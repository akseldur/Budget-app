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


def _auth_headers(application_id: str, private_key_path: str) -> dict[str, str]:
    token = build_jwt(application_id, private_key_path)
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def get_application_status(application_id: str, private_key_path: str) -> httpx.Response:
    return httpx.get(
        f"{API_BASE_URL}/application",
        headers=_auth_headers(application_id, private_key_path),
        timeout=15,
    )


def start_authorization(
    application_id: str,
    private_key_path: str,
    *,
    aspsp_name: str,
    aspsp_country: str,
    redirect_url: str,
    state: str,
    valid_until: str,
    psu_type: str = "personal",
) -> httpx.Response:
    return httpx.post(
        f"{API_BASE_URL}/auth",
        headers=_auth_headers(application_id, private_key_path),
        json={
            "access": {"valid_until": valid_until},
            "aspsp": {"name": aspsp_name, "country": aspsp_country},
            "state": state,
            "redirect_url": redirect_url,
            "psu_type": psu_type,
        },
        timeout=15,
    )


def exchange_code_for_session(application_id: str, private_key_path: str, code: str) -> httpx.Response:
    return httpx.post(
        f"{API_BASE_URL}/sessions",
        headers=_auth_headers(application_id, private_key_path),
        json={"code": code},
        timeout=15,
    )


def get_balances(application_id: str, private_key_path: str, account_uid: str) -> httpx.Response:
    return httpx.get(
        f"{API_BASE_URL}/accounts/{account_uid}/balances",
        headers=_auth_headers(application_id, private_key_path),
        timeout=15,
    )


def get_transactions(
    application_id: str,
    private_key_path: str,
    account_uid: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    continuation_key: str | None = None,
) -> httpx.Response:
    params = {
        k: v
        for k, v in {
            "date_from": date_from,
            "date_to": date_to,
            "continuation_key": continuation_key,
        }.items()
        if v is not None
    }
    return httpx.get(
        f"{API_BASE_URL}/accounts/{account_uid}/transactions",
        headers=_auth_headers(application_id, private_key_path),
        params=params,
        timeout=15,
    )
