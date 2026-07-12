import pytest
from fastapi.testclient import TestClient


def test_apply_for_loan(client: TestClient, auth_headers):
    # Create customer first
    customer_response = client.post("/api/v1/customers", json={
        "full_name": "Loan Customer",
        "phone": "0733445566",
        "national_id": "22334455",
    }, headers=auth_headers)
    
    customer_id = customer_response.json()["id"]
    
    # Apply for loan
    response = client.post("/api/v1/loans/apply", json={
        "customer_id": customer_id,
        "amount": 50000.0,
        "interest_rate": 0.15,
        "term_months": 3,
    }, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 50000.0
    assert data["status"] == "PENDING"


def test_loan_decision_mpesa(client: TestClient, auth_headers):
    # Create customer
    customer_response = client.post("/api/v1/customers", json={
        "full_name": "Decision Customer",
        "phone": "0744556677",
        "national_id": "33445566",
        "income": 60000.0,
    }, headers=auth_headers)
    
    customer_id = customer_response.json()["id"]
    
    # Request decision
    response = client.post("/api/v1/loans/decision/mpesa", json={
        "customer_id": customer_id,
        "amount": 30000.0,
        "term_months": 2,
        "statement_type": "mpesa",
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "credit_score" in data
    assert "probability_of_default" in data


# TODO: Add loan approval tests
# TODO: Add loan rejection tests
# TODO: Add portfolio summary tests