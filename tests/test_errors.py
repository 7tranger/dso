from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert body["status"] == 404
    assert body["type"] == "/problems/not_found"
    assert body["title"] == "Application error"
    assert "correlation_id" in body


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    assert r.headers.get("content-type", "").startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 422
    assert body["type"] == "/problems/validation_error"
    assert body["title"] == "Validation error"
    assert "correlation_id" in body
