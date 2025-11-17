import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

import httpx
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.http_client import ExternalServiceError, SafeHttpClient
from src.services.secrets import get_secret

client = TestClient(app)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_user_and_board() -> tuple[str, int]:
    email = f"user-{datetime.now(timezone.utc).timestamp()}@example.com"
    password = "password123"
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = resp.json()["access_token"]
    resp = client.post(
        "/api/v1/boards",
        json={"title": "Secure board"},
        headers=_auth_headers(token),
    )
    board_id = resp.json()["id"]
    return token, board_id


def test_card_validation_rejects_invalid_estimate():
    token, board_id = _create_user_and_board()
    payload = {
        "title": "Bad estimate",
        "column": "backlog",
        "order_idx": 0,
        "board_id": board_id,
        "estimate_hours": -1,  # invalid
    }
    resp = client.post("/api/v1/cards", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"


def test_safe_http_client_timeout_raises_external_error():
    safe_client = SafeHttpClient(base_url="https://example.com", retries=3)
    with mock.patch.object(safe_client._client, "request", side_effect=httpx.TimeoutException("boom")) as mocked:
        with pytest.raises(ExternalServiceError):
            safe_client.request("GET", "/score")
        assert mocked.call_count == 3  # ensures retries triggered


def test_missing_secret_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        get_secret("JWT_SECRET")
    os.environ["JWT_SECRET"] = "test-super-secret-key-1234567890"


def test_secret_masking_prevents_logging_plain_value(caplog, monkeypatch):
    monkeypatch.setenv("A_CUSTOM_SECRET", "super-secret-value-1234567890")
    secret = get_secret("A_CUSTOM_SECRET")
    caplog.set_level(logging.INFO)
    logging.getLogger("tests").info("Using secret %s", secret)
    assert "super-secret-value-1234567890" not in caplog.text


