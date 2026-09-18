"""Minimal bootstrap/smoke test: confirms the FastAPI app starts and the
health-check route responds. Not a feature test - this project has no
business endpoints yet.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
