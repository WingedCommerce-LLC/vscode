"""
Test configuration and fixtures for Overseer test suite.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import our application and dependencies
from api.main import app
from database import get_db, get_async_db
from models.base import Base
from models.user import User, UserRole
from models.team import Team
from auth.password import get_password_hash
from config.settings import get_settings

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_overseer.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test_overseer.db"

# Create test engines
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

test_sync_engine = create_engine(
    TEST_SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session factory
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestingSessionLocal() as session:
        yield session

    # Clean up - drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db and get_async_db dependencies to use test database."""
    async def _override_get_async_db():
        yield db_session

    def _override_get_db():
        # This is for any sync endpoints that might still use get_db
        yield db_session

    app.dependency_overrides[get_async_db] = _override_get_async_db
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db) -> TestClient:
    """Create a test client with database override."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""
    async with AsyncClient(base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.MEMBER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_director(db_session: AsyncSession) -> User:
    """Create a test director user."""
    director = User(
        username="director",
        email="director@example.com",
        password_hash=get_password_hash("directorpassword123"),
        role=UserRole.DIRECTOR,
        is_active=True
    )
    db_session.add(director)
    await db_session.commit()
    await db_session.refresh(director)
    return director


@pytest_asyncio.fixture
async def test_team(db_session: AsyncSession, test_director: User) -> Team:
    """Create a test team."""
    team = Team(
        name="Test Team",
        description="A test team for testing purposes",
        owner_id=test_director.id
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: TestClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_admin.username,
            "password": "adminpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def director_headers(client: TestClient, test_director: User) -> dict:
    """Get authentication headers for director user."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_director.username,
            "password": "directorpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Test data factories
class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    async def create_user(
        db_session: AsyncSession,
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword123",
        role: UserRole = UserRole.MEMBER,
        is_active: bool = True
    ) -> User:
        """Create a test user with specified parameters."""
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            is_active=is_active
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user


class TeamFactory:
    """Factory for creating test teams."""

    @staticmethod
    async def create_team(
        db_session: AsyncSession,
        name: str = "Test Team",
        description: str = "A test team",
        owner: User = None
    ) -> Team:
        """Create a test team with specified parameters."""
        if owner is None:
            # Create a default owner
            owner = await UserFactory.create_user(
                db_session,
                username="teamowner",
                email="owner@example.com",
                role=UserRole.DIRECTOR
            )

        team = Team(
            name=name,
            description=description,
            owner_id=owner.id
        )
        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)
        return team


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def assert_user_response(response_data: dict, expected_user: User):
        """Assert that user response data matches expected user."""
        assert response_data["id"] == str(expected_user.id)
        assert response_data["username"] == expected_user.username
        assert response_data["email"] == expected_user.email
        assert response_data["role"] == expected_user.role.value
        assert response_data["is_active"] == expected_user.is_active
        assert "password_hash" not in response_data

    @staticmethod
    def assert_team_response(response_data: dict, expected_team: Team):
        """Assert that team response data matches expected team."""
        assert response_data["id"] == str(expected_team.id)
        assert response_data["name"] == expected_team.name
        assert response_data["description"] == expected_team.description
        assert response_data["owner_id"] == str(expected_team.owner_id)

    @staticmethod
    def assert_error_response(response_data: dict, expected_status: int, expected_message: str = None):
        """Assert that error response has expected structure."""
        assert "error" in response_data
        assert response_data["error"]["status_code"] == expected_status
        if expected_message:
            assert expected_message in response_data["error"]["message"]
        assert "timestamp" in response_data
        assert "request" in response_data


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add markers based on test name
        if "auth" in item.name:
            item.add_marker(pytest.mark.auth)
        if "api" in item.name:
            item.add_marker(pytest.mark.api)
