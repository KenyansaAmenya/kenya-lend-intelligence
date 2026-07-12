import pytest
from fastapi.testclient import TestClient


def test_predict_churn(client: TestClient, auth_headers):
    # Create customer
    customer_response = client.post("/api/v1/customers", json={
        "full_name": "Churn Customer",
        "phone": "0755667788",
        "national_id": "44556677",
    }, headers=auth_headers)
    
    customer_id = customer_response.json()["id"]
    
    # Predict churn
    response = client.post("/api/v1/churn/predict", json={
        "customer_id": customer_id,
        "lookback_days": 90,
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "probability_of_churn" in data
    assert "risk_level" in data
    assert "churn_drivers" in data


def test_get_at_risk_customers(client: TestClient, auth_headers):
    response = client.get("/api/v1/churn/customers/at-risk?threshold=0.5&limit=50", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_customer_segments(client: TestClient, auth_headers):
    response = client.get("/api/v1/churn/customers/segments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


# TODO: Add batch prediction tests
# TODO: Add retention recommendation tests
# TODO: Add churn trend tests