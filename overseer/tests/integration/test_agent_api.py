"""
Integration tests for Agent API endpoints.

Tests agent registration, management, status tracking, and approval workflows.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.team import Team
from models.agent import Agent, AgentStatus, AgentType


class TestAgentRegistration:
    """Test agent registration functionality."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_register_agent_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test successful agent registration."""
        agent_data = {
            "name": "Test Agent",
            "description": "A test AI agent",
            "type": "coder",
            "capabilities": ["python", "javascript", "testing"],
            "version": "1.0.0"
        }

        response = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == agent_data["name"]
        assert data["description"] == agent_data["description"]
        assert data["type"] == agent_data["type"]
        assert data["capabilities"] == agent_data["capabilities"]
        assert data["version"] == agent_data["version"]
        assert data["owner_id"] == str(test_user.id)
        assert data["status"] == "inactive"
        assert data["is_approved"] is False  # Regular users need approval

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_register_agent_admin_auto_approve(
        self,
        async_client: AsyncClient,
        test_admin: User,
        admin_headers: dict
    ):
        """Test that admin users get auto-approved agents."""
        agent_data = {
            "name": "Admin Agent",
            "description": "An admin's AI agent",
            "type": "general"
        }

        response = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=admin_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_approved"] is True  # Admins get auto-approval

    @pytest.mark.asyncio
    async def test_register_agent_duplicate_name(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test that duplicate agent names are rejected."""
        agent_data = {
            "name": "Duplicate Agent",
            "type": "general"
        }

        # Register first agent
        response1 = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=auth_headers
        )
        assert response1.status_code == 201

        # Try to register duplicate
        response2 = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=auth_headers
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_agent_with_team(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_team: Team,
        auth_headers: dict
    ):
        """Test registering agent with team assignment."""
        agent_data = {
            "name": "Team Agent",
            "type": "general",
            "team_id": str(test_team.id)
        }

        response = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["team_id"] == str(test_team.id)

    @pytest.mark.asyncio
    async def test_register_agent_invalid_team(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test registering agent with invalid team ID."""
        agent_data = {
            "name": "Invalid Team Agent",
            "type": "general",
            "team_id": str(uuid.uuid4())
        }

        response = await async_client.post(
            "/api/agents/register",
            json=agent_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_agent_validation_errors(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test agent registration validation."""
        # Empty name
        response = await async_client.post(
            "/api/agents/register",
            json={"name": "", "type": "general"},
            headers=auth_headers
        )
        assert response.status_code == 422

        # Invalid type
        response = await async_client.post(
            "/api/agents/register",
            json={"name": "Test", "type": "invalid_type"},
            headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_agent_unauthorized(
        self,
        async_client: AsyncClient
    ):
        """Test that agent registration requires authentication."""
        agent_data = {
            "name": "Unauthorized Agent",
            "type": "general"
        }

        response = await async_client.post(
            "/api/agents/register",
            json=agent_data
        )

        assert response.status_code == 401


class TestAgentListing:
    """Test agent listing and filtering functionality."""

    @pytest.mark.asyncio
    async def test_list_agents_basic(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test basic agent listing."""
        response = await async_client.get(
            "/api/agents/",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert len(data["agents"]) >= 1

        # Check that user can see their own agent
        agent_ids = [agent["id"] for agent in data["agents"]]
        assert str(test_agent.id) in agent_ids

    @pytest.mark.asyncio
    async def test_list_agents_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test agent listing pagination."""
        response = await async_client.get(
            "/api/agents/?page=1&per_page=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert len(data["agents"]) <= 5

    @pytest.mark.asyncio
    async def test_list_agents_filtering(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test agent listing with filters."""
        # Filter by type
        response = await async_client.get(
            f"/api/agents/?type={test_agent.type}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Filter by status
        response = await async_client.get(
            f"/api/agents/?status={test_agent.status}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Filter by approval status
        response = await async_client.get(
            f"/api/agents/?is_approved={str(test_agent.is_approved).lower()}",
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_agents_search(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test agent search functionality."""
        response = await async_client.get(
            f"/api/agents/?query={test_agent.name[:5]}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should find the agent by partial name match
        agent_names = [agent["name"] for agent in data["agents"]]
        assert any(test_agent.name in name for name in agent_names)


class TestAgentManagement:
    """Test agent management operations."""

    @pytest.mark.asyncio
    async def test_get_agent_success(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test getting a specific agent."""
        response = await async_client.get(
            f"/api/agents/{test_agent.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_agent.id)
        assert data["name"] == test_agent.name

    @pytest.mark.asyncio
    async def test_get_agent_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting non-existent agent."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/agents/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_agent_success(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test updating agent information."""
        update_data = {
            "name": "Updated Agent Name",
            "description": "Updated description",
            "capabilities": ["python", "updated-skill"]
        }

        response = await async_client.put(
            f"/api/agents/{test_agent.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["capabilities"] == update_data["capabilities"]

    @pytest.mark.asyncio
    async def test_delete_agent_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test deleting an agent."""
        # Create a test agent to delete
        agent = Agent(
            name="Agent to Delete",
            type=AgentType.GENERAL.value,
            owner_id=test_user.id,
            status=AgentStatus.INACTIVE.value
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        response = await async_client.delete(
            f"/api/agents/{agent.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify agent is deleted
        response = await async_client.get(
            f"/api/agents/{agent.id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAgentApproval:
    """Test agent approval workflow."""

    @pytest.mark.asyncio
    async def test_approve_agent_success(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        admin_headers: dict
    ):
        """Test approving an agent."""
        approval_data = {
            "approved": True,
            "reason": "Agent meets requirements"
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/approve",
            json=approval_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_approved"] is True

    @pytest.mark.asyncio
    async def test_reject_agent(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        admin_headers: dict
    ):
        """Test rejecting an agent."""
        approval_data = {
            "approved": False,
            "reason": "Agent does not meet requirements"
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/approve",
            json=approval_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_approved"] is False

    @pytest.mark.asyncio
    async def test_approve_agent_unauthorized(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test that regular users cannot approve agents."""
        approval_data = {"approved": True}

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/approve",
            json=approval_data,
            headers=auth_headers
        )

        assert response.status_code == 403


class TestAgentStatus:
    """Test agent status management."""

    @pytest.mark.asyncio
    async def test_update_agent_status_success(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test updating agent status."""
        status_data = {
            "status": "active"
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/status",
            json=status_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["last_active"] is not None

    @pytest.mark.asyncio
    async def test_update_agent_status_with_error(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test updating agent status to error with message."""
        status_data = {
            "status": "error",
            "error_message": "Agent encountered an error"
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/status",
            json=status_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error_message"] == status_data["error_message"]

    @pytest.mark.asyncio
    async def test_update_agent_status_error_without_message(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test that error status requires error message."""
        status_data = {
            "status": "error"
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/status",
            json=status_data,
            headers=auth_headers
        )

        assert response.status_code == 422


class TestAgentHeartbeat:
    """Test agent heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_agent_heartbeat_success(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test sending agent heartbeat."""
        heartbeat_data = {
            "status": "active",
            "performance_metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "tasks_completed": 15
            },
            "active_tasks": 2
        }

        response = await async_client.post(
            f"/api/agents/{test_agent.id}/heartbeat",
            json=heartbeat_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_agent_heartbeat_minimal(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test sending minimal heartbeat."""
        response = await async_client.post(
            f"/api/agents/{test_agent.id}/heartbeat",
            json={},
            headers=auth_headers
        )

        assert response.status_code == 200


class TestAgentStats:
    """Test agent statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_agent_stats_success(
        self,
        async_client: AsyncClient,
        admin_headers: dict
    ):
        """Test getting agent statistics."""
        response = await async_client.get(
            "/api/agents/stats/overview",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = [
            "total_agents", "active_agents", "inactive_agents",
            "busy_agents", "error_agents", "maintenance_agents",
            "approved_agents", "pending_approval", "by_type", "by_team"
        ]
        for field in required_fields:
            assert field in data

        # Check that counts are non-negative integers
        for field in required_fields[:-2]:  # Exclude by_type and by_team
            assert isinstance(data[field], int)
            assert data[field] >= 0

    @pytest.mark.asyncio
    async def test_get_agent_stats_unauthorized(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that regular users cannot access agent stats."""
        response = await async_client.get(
            "/api/agents/stats/overview",
            headers=auth_headers
        )

        assert response.status_code == 403


class TestAgentPermissions:
    """Test agent access permissions."""

    @pytest.mark.asyncio
    async def test_agent_owner_permissions(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        auth_headers: dict
    ):
        """Test that agent owners have full access."""
        # Owner can view
        response = await async_client.get(
            f"/api/agents/{test_agent.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Owner can update
        response = await async_client.put(
            f"/api/agents/{test_agent.id}",
            json={"description": "Updated by owner"},
            headers=auth_headers
        )
        assert response.status_code == 200

        # Owner can delete
        response = await async_client.delete(
            f"/api/agents/{test_agent.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_admin_permissions(
        self,
        async_client: AsyncClient,
        test_agent: Agent,
        admin_headers: dict
    ):
        """Test that admins have full access to all agents."""
        # Admin can view any agent
        response = await async_client.get(
            f"/api/agents/{test_agent.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

        # Admin can update any agent
        response = await async_client.put(
            f"/api/agents/{test_agent.id}",
            json={"description": "Updated by admin"},
            headers=admin_headers
        )
        assert response.status_code == 200
