from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_ready_without_database():
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not available"
