"""
Test authentication functionality using proper async test configuration.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from models.user import User, UserRole
from auth.password import get_password_hash


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "member"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["role"] == "member"
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_user(async_client: AsyncClient):
    """Test registering a user with duplicate username."""
    # First registration
    await async_client.post(
        "/api/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate1@example.com",
            "password": "testpassword123",
            "role": "member"
        }
    )

    # Second registration with same username
    response = await async_client.post(
        "/api/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate2@example.com",
            "password": "testpassword123",
            "role": "member"
        }
    )
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user(async_client: AsyncClient):
    """Test user login."""
    # First register a user
    await async_client.post(
        "/api/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "testpassword123",
            "role": "member"
        }
    )

    # Then login
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "loginuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    """Test login with invalid credentials."""
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient):
    """Test getting current user info."""
    # Register and login
    await async_client.post(
        "/api/auth/register",
        json={
            "username": "currentuser",
            "email": "current@example.com",
            "password": "testpassword123",
            "role": "member"
        }
    )

    login_response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "currentuser",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"
    assert data["email"] == "current@example.com"
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(async_client: AsyncClient):
    """Test getting current user with invalid token."""
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_verification(async_client: AsyncClient):
    """Test token verification endpoint."""
    # Register and login to get token
    await async_client.post(
        "/api/auth/register",
        json={
            "username": "verifyuser",
            "email": "verify@example.com",
            "password": "verifypassword123",
            "role": "member"
        }
    )

    login_response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "verifyuser",
            "password": "verifypassword123"
        }
    )

    token = login_response.json()["access_token"]

    # Verify token
    response = await async_client.get(
        "/api/auth/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["username"] == "verifyuser"
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    """Test token refresh functionality."""
    # Register and login to get tokens
    await async_client.post(
        "/api/auth/register",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "refreshpassword123",
            "role": "member"
        }
    )

    login_response = await async_client.post(
        "/api/auth/login",
        data={
            "username": "refreshuser",
            "password": "refreshpassword123"
        }
    )

    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token to get new access token
    response = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
