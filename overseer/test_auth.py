"""
Basic authentication system tests for Overseer platform.

This module provides basic tests to verify the authentication system is working correctly.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from database import get_db
from models.base import Base
from models.user import User, UserRole
from auth.password import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


def setup_module():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)


def teardown_module():
    """Clean up test database."""
    Base.metadata.drop_all(bind=engine)


def test_user_registration():
    """Test user registration endpoint."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "MEMBER"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["role"] == "MEMBER"
    assert data["is_active"] is True


def test_user_login():
    """Test user login endpoint."""
    # First register a user
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpassword123",
            "role": "MEMBER"
        }
    )

    # Then login
    response = client.post(
        "/auth/login",
        data={
            "username": "loginuser",
            "password": "loginpassword123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == "loginuser"


def test_protected_endpoint():
    """Test accessing protected endpoint with valid token."""
    # Register and login to get token
    client.post(
        "/auth/register",
        json={
            "username": "protecteduser",
            "email": "protected@example.com",
            "password": "protectedpassword123",
            "role": "MEMBER"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "protecteduser",
            "password": "protectedpassword123"
        }
    )

    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "protecteduser"
    assert data["email"] == "protected@example.com"


def test_invalid_login():
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_token_verification():
    """Test token verification endpoint."""
    # Register and login to get token
    client.post(
        "/auth/register",
        json={
            "username": "verifyuser",
            "email": "verify@example.com",
            "password": "verifypassword123",
            "role": "MEMBER"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "verifyuser",
            "password": "verifypassword123"
        }
    )

    token = login_response.json()["access_token"]

    # Verify token
    response = client.get(
        "/auth/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["username"] == "verifyuser"
    assert data["role"] == "MEMBER"


if __name__ == "__main__":
    # Run basic tests
    setup_module()

    try:
        test_user_registration()
        print("✓ User registration test passed")

        test_user_login()
        print("✓ User login test passed")

        test_protected_endpoint()
        print("✓ Protected endpoint test passed")

        test_invalid_login()
        print("✓ Invalid login test passed")

        test_unauthorized_access()
        print("✓ Unauthorized access test passed")

        test_token_verification()
        print("✓ Token verification test passed")

        print("\n🎉 All authentication tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        teardown_module()
