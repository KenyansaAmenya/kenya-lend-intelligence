# Authentication Tests.

import pytest
from fastapi.testclient import TestClient

def test_register_user(client: TestClient):
    response = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "password" not in data


def test_register_duplicate_email(client: TestClient):
    # First registration
    client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123",
        "full_name": "Dup User",
    })
    
    # Duplicate
    response = client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123",
        "full_name": "Dup User 2",
    })
    assert response.status_code == 422


def test_login_success(client: TestClient):
    # Register first
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "SecurePass123",
        "full_name": "Login User",
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "login@example.com",
        "password": "SecurePass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    response = client.post("/api/v1/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "WrongPass123",
    })
    assert response.status_code == 401


def test_get_current_user(client: TestClient, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


# TODO: Add MFA test cases
# TODO: Add password reset flow tests
# TODO: Add token refresh tests