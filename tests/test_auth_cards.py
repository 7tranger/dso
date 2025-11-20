from fastapi.testclient import TestClient

from src.adapters.db import Base, engine
from src.main import app

client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(
    email: str = "user@example.com", password: str = "password123", reset: bool = True
) -> str:
    if reset:
        reset_db()
    r = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert r.status_code == 201

    r = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    body = r.json()
    return body["access_token"]


def test_register_and_login_and_create_card():
    token = register_and_login()

    # Create board
    r = client.post(
        "/api/v1/boards",
        json={"title": "My Ideas"},
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    board = r.json()

    # Create card
    r = client.post(
        "/api/v1/cards",
        json={
            "title": "First idea",
            "column": "backlog",
            "order_idx": 0,
            "board_id": board["id"],
        },
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    card = r.json()
    assert card["title"] == "First idea"
    assert card["column"] == "backlog"
    assert card["board_id"] == board["id"]

    # List cards
    r = client.get("/api/v1/cards", headers=auth_headers(token))
    assert r.status_code == 200
    cards = r.json()
    assert len(cards) == 1


def test_owner_only_access():
    token_owner = register_and_login("owner@example.com", "password123")

    # create board and card as owner
    r = client.post(
        "/api/v1/boards",
        json={"title": "Owner board"},
        headers=auth_headers(token_owner),
    )
    board_id = r.json()["id"]

    r = client.post(
        "/api/v1/cards",
        json={
            "title": "Secret idea",
            "column": "backlog",
            "order_idx": 0,
            "board_id": board_id,
        },
        headers=auth_headers(token_owner),
    )
    card_id = r.json()["id"]

    # second user
    token_other = register_and_login("other@example.com", "password123", reset=False)

    r = client.get(f"/api/v1/cards/{card_id}", headers=auth_headers(token_other))
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == "FORBIDDEN"


def test_login_invalid_credentials_returns_structured_error():
    reset_db()

    # no registration, immediate login
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "no-user@example.com", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 400
    body = r.json()
    assert body["code"] == "INVALID_CREDENTIALS"
    assert "message" in body
    assert "details" in body


def test_unauthorized_access_returns_structured_error():
    reset_db()

    r = client.get("/api/v1/cards")
    assert r.status_code == 401
    body = r.json()
    assert body["code"] == "UNAUTHORIZED"
    assert "message" in body
    assert "details" in body


def test_validation_error_for_cards_payload_is_structured():
    token = register_and_login("val@example.com", "password123")

    # invalid column value triggers Pydantic/validation
    r = client.post(
        "/api/v1/cards",
        json={
            "title": "Bad column",
            "column": "unknown",  # invalid
            "order_idx": 0,
            "board_id": 1,
        },
        headers=auth_headers(token),
    )
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "details" in body
    assert "errors" in body["details"]
