import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_png_bytes(width: int = 1, height: int = 1) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"rest"


def test_upload_png_ok_and_uuid_name():
    data = make_png_bytes()
    files = {"file": ("../../evil.png", io.BytesIO(data), "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["content_type"] == "image/png"
    assert body["size"] == len(data)
    assert body["stored_filename"].endswith(".png")
    assert len(body["stored_filename"].split(".")[0]) == 32


def test_upload_rejects_large_file():
    big = b"\x89PNG\r\n\x1a\n" + b"a" * (1_000_000 + 10)
    files = {"file": ("big.png", io.BytesIO(big), "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 413
    assert r.headers.get("content-type", "").startswith("application/problem+json")
    body = r.json()
    assert body["type"] == "/problems/payload_too_large"
    assert body["title"] == "Payload Too Large"
    assert body["status"] == 413
    assert "correlation_id" in body


def test_upload_rejects_wrong_signature():
    bad = b"not-a-png"  # wrong magic
    files = {"file": ("f.png", io.BytesIO(bad), "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 422
    body = r.json()
    assert body["type"] == "/problems/invalid_signature"
    assert body["status"] == 422
    assert body["title"] == "Validation error"
