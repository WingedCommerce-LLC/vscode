"""
Integration tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from tests.conftest import TestUtils


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_user_registration_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword123",
                "role": "MEMBER"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "MEMBER"
        assert data["is_active"] is True
        assert "password_hash" not in data
        assert "id" in data

    def test_user_registration_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with duplicate username."""
        response = client.post(
            "/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123",
                "role": "MEMBER"
            }
        )

        assert response.status_code == 400
        TestUtils.assert_error_response(response.json(), 400, "Username already registered")

    def test_user_registration_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email."""
        response = client.post(
            "/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "password123",
                "role": "MEMBER"
            }
        )

        assert response.status_code == 400
        TestUtils.assert_error_response(response.json(), 400, "Email already registered")

    def test_user_registration_invalid_data(self, client: TestClient):
        """Test registration with invalid data."""
        response = client.post(
            "/auth/register",
            json={
                "username": "",  # Empty username
                "email": "invalid-email",  # Invalid email
                "password": "123",  # Too short password
                "role": "INVALID_ROLE"  # Invalid role
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "ValidationError"

    def test_user_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user.username

    def test_user_login_invalid_username(self, client: TestClient):
        """Test login with invalid username."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401, "Incorrect username or password")

    def test_user_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401, "Incorrect username or password")

    def test_user_login_inactive_user(self, client: TestClient, db_session: AsyncSession):
        """Test login with inactive user."""
        # This would require creating an inactive user fixture or modifying existing one
        pass  # Skip for now, can be implemented later

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict):
        """Test getting current user with valid token."""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "MEMBER"
        assert "password_hash" not in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401)

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401)

    def test_token_verification_success(self, client: TestClient, auth_headers: dict):
        """Test token verification with valid token."""
        response = client.get("/auth/verify-token", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "testuser"
        assert data["role"] == "MEMBER"

    def test_token_verification_invalid_token(self, client: TestClient):
        """Test token verification with invalid token."""
        response = client.get(
            "/auth/verify-token",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401)

    def test_token_refresh_success(self, client: TestClient, test_user: User):
        """Test token refresh with valid refresh token."""
        # First login to get refresh token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_token_refresh_invalid_token(self, client: TestClient):
        """Test token refresh with invalid refresh token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401)

    def test_user_logout_success(self, client: TestClient, auth_headers: dict):
        """Test user logout with valid token."""
        response = client.post("/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_user_logout_no_token(self, client: TestClient):
        """Test user logout without token."""
        response = client.post("/auth/logout")

        assert response.status_code == 401
        TestUtils.assert_error_response(response.json(), 401)

    def test_authentication_flow_complete(self, client: TestClient):
        """Test complete authentication flow: register -> login -> access protected -> logout."""
        # 1. Register new user
        register_response = client.post(
            "/auth/register",
            json={
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "flowpassword123",
                "role": "MEMBER"
            }
        )
        assert register_response.status_code == 201

        # 2. Login with new user
        login_response = client.post(
            "/auth/login",
            data={
                "username": "flowuser",
                "password": "flowpassword123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Access protected endpoint
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowuser"

        # 4. Verify token
        verify_response = client.get("/auth/verify-token", headers=headers)
        assert verify_response.status_code == 200
        assert verify_response.json()["valid"] is True

        # 5. Logout
        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
