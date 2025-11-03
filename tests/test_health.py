from fastapi.testclient import TestClient

from app.main import app, validate_and_format_name

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_validate_and_format_name_basic():
    assert validate_and_format_name("hello world") == "hello world"
    assert validate_and_format_name("  test  ") == "test"
    assert validate_and_format_name("hello@world#123") == "hello@world#123"


def test_validate_and_format_name_empty():
    from app.main import ApiError

    try:
        validate_and_format_name("")
        assert False, "Should raise ApiError"
    except ApiError as e:
        assert "name cannot be empty" in e.message


def test_validate_and_format_name_short():
    from app.main import ApiError

    try:
        validate_and_format_name("   ")
        assert False, "Should raise ApiError"
    except ApiError as e:
        assert "name too short" in e.message
