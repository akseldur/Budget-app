"""Tester for tolkning av feilresponser fra Enable Banking (app/integrations/errors.py)."""

import httpx
import pytest
from fastapi import HTTPException

from app.integrations.errors import parse_upstream_error, raise_for_enablebanking_error


def test_200_gir_ingen_feil():
    response = httpx.Response(status_code=200, json={"ok": True})
    raise_for_enablebanking_error(response)  # skal ikke kaste noe


def test_401_flagges_som_reconnect_required():
    response = httpx.Response(status_code=401, json={"error": "UNAUTHORIZED"})

    with pytest.raises(HTTPException) as exc_info:
        raise_for_enablebanking_error(response)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["reconnect_required"] is True


def test_403_flagges_som_reconnect_required():
    response = httpx.Response(status_code=403, json={"error": "FORBIDDEN"})

    with pytest.raises(HTTPException) as exc_info:
        raise_for_enablebanking_error(response)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["reconnect_required"] is True


def test_404_gir_generisk_upstream_feil_uten_reconnect():
    response = httpx.Response(status_code=404, json={"error": "ACCOUNT_DOES_NOT_EXIST"})

    with pytest.raises(HTTPException) as exc_info:
        raise_for_enablebanking_error(response)

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["reconnect_required"] is False
    assert exc_info.value.detail["upstream"]["error"] == "ACCOUNT_DOES_NOT_EXIST"


def test_parse_upstream_error_med_gyldig_json():
    response = httpx.Response(status_code=422, json={"error": "WRONG_REQUEST_PARAMETERS"})
    assert parse_upstream_error(response) == {"error": "WRONG_REQUEST_PARAMETERS"}


def test_parse_upstream_error_uten_json_faller_tilbake_pa_tekst():
    response = httpx.Response(status_code=500, text="internal server error")
    assert parse_upstream_error(response) == {"message": "internal server error"}
