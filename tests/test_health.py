from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_correlation_id_header_present():
    r = client.get("/health", headers={"X-Correlation-Id": "abc123"})
    assert r.status_code == 200
    assert r.headers.get("X-Correlation-Id") == "abc123"
