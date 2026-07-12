import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_async_db
from app.main import app


# Test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/kenya_lend_test"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    # Register test user
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User",
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123",
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# TODO: Add factory fixtures for test data
# TODO: Add mock Supabase fixture
# TODO: Add mock ML model fixture