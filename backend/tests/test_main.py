from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_info(monkeypatch):
    monkeypatch.setenv("APP_MESSAGE", "Test message")
    response = client.get("/api/info")

    assert response.status_code == 200
    assert response.json()["message"] == "Test message"
    assert response.json()["backend"] == "python-fastapi"


def test_health():
    assert client.get("/healthz").json() == {"status": "healthy"}


def test_readiness_requires_secret(monkeypatch):
    monkeypatch.delenv("APP_TOKEN", raising=False)
    response = client.get("/readyz")

    assert response.status_code == 503


def test_readiness_with_secret(monkeypatch):
    monkeypatch.setenv("APP_TOKEN", "test-only")
    response = client.get("/readyz")

    assert response.status_code == 200
