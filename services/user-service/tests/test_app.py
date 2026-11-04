import sys
from pathlib import Path

# Add the service directory to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))




from app import app


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_create_user_validation():
    client = app.test_client()

    response = client.post("/users", json={})

    assert response.status_code == 400
