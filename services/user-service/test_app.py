from app import app


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_create_order_validation():
    client = app.test_client()

    response = client.post("/orders", json={})

    assert response.status_code == 400
