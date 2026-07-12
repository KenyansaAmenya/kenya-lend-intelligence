import pytest
from fastapi.testclient import TestClient


def test_create_customer(client: TestClient, auth_headers):
    response = client.post("/api/v1/customers", json={
        "full_name": "John Doe",
        "phone": "0712345678",
        "national_id": "12345678",
        "location": "Nairobi",
        "occupation": "Software Developer",
        "employment_status": "EMPLOYED",
        "income": 80000.0,
    }, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert data["phone"] == "0712345678"


def test_create_customer_invalid_phone(client: TestClient, auth_headers):
    response = client.post("/api/v1/customers", json={
        "full_name": "Jane Doe",
        "phone": "invalid",
        "national_id": "87654321",
    }, headers=auth_headers)
    
    assert response.status_code == 422


def test_list_customers(client: TestClient, auth_headers):
    response = client.get("/api/v1/customers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_customer(client: TestClient, auth_headers):
    # Create customer first
    create_response = client.post("/api/v1/customers", json={
        "full_name": "Test Customer",
        "phone": "0722334455",
        "national_id": "11223344",
    }, headers=auth_headers)
    
    customer_id = create_response.json()["id"]
    
    # Get customer
    response = client.get(f"/api/v1/customers/{customer_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test Customer"


# TODO: Add customer update tests
# TODO: Add customer search tests
# TODO: Add customer health score tests