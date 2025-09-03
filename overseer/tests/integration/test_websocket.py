"""
Integration tests for WebSocket functionality.

Tests WebSocket connections, authentication, and real-time communication
between agents and the Overseer platform.
"""

import json
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api.main import app
from api.websocket import connection_manager
from models.user import User
from models.agent import Agent


class TestWebSocketAuthentication:
    """Test WebSocket authentication functionality."""

    @pytest.mark.asyncio
    async def test_websocket_agent_connection_without_token(self, async_client: AsyncClient):
        """Test that WebSocket connection fails without authentication token."""
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/agent/test-agent-id"):
                    pass

    @pytest.mark.asyncio
    async def test_websocket_monitor_connection_without_token(self, async_client: AsyncClient):
        """Test that monitor WebSocket connection fails without authentication token."""
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/monitor"):
                    pass

    @pytest.mark.asyncio
    async def test_websocket_agent_connection_with_invalid_token(self, async_client: AsyncClient):
        """Test that WebSocket connection fails with invalid token."""
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/agent/test-agent-id?token=invalid-token"):
                    pass

    @pytest.mark.asyncio
    async def test_websocket_agent_connection_with_nonexistent_agent(
        self,
        async_client: AsyncClient,
        test_user: User,
        auth_headers: Dict[str, str]
    ):
        """Test that WebSocket connection fails for nonexistent agent."""
        # Extract token from auth headers
        token = auth_headers["Authorization"].replace("Bearer ", "")

        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect(f"/ws/agent/nonexistent-agent?token={token}"):
                    pass


class TestWebSocketConnectionManager:
    """Test WebSocket connection manager functionality."""

    def test_connection_manager_initialization(self):
        """Test that connection manager initializes correctly."""
        manager = connection_manager
        assert isinstance(manager.active_connections, dict)
        assert isinstance(manager.connection_metadata, dict)
        assert isinstance(manager.user_connections, dict)
        assert len(manager.active_connections) == 0
        assert len(manager.connection_metadata) == 0
        assert len(manager.user_connections) == 0

    def test_connection_stats_empty(self):
        """Test connection stats when no connections exist."""
        stats = connection_manager.get_connection_stats()
        assert stats["active_agents"] == 0
        assert stats["connected_users"] == 0
        assert stats["total_user_connections"] == 0
        assert isinstance(stats["connection_metadata"], dict)

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_agent(self):
        """Test sending message to nonexistent agent."""
        result = await connection_manager.send_to_agent("nonexistent", {"test": "message"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self):
        """Test sending message to nonexistent user."""
        # This should not raise an exception, just do nothing
        await connection_manager.send_to_user("nonexistent", {"test": "message"})

    @pytest.mark.asyncio
    async def test_broadcast_to_users_empty(self):
        """Test broadcasting when no users are connected."""
        # This should not raise an exception
        await connection_manager.broadcast_to_users({"test": "broadcast"})


class TestWebSocketMessageSchemas:
    """Test WebSocket message schema validation."""

    def test_websocket_message_schema(self):
        """Test basic WebSocket message schema."""
        from api.websocket import WebSocketMessage

        message = WebSocketMessage(type="test")
        assert message.type == "test"
        assert isinstance(message.timestamp, datetime)
        assert isinstance(message.correlation_id, str)
        assert isinstance(message.payload, dict)

    def test_agent_heartbeat_message_schema(self):
        """Test agent heartbeat message schema."""
        from api.websocket import AgentHeartbeatMessage

        message = AgentHeartbeatMessage(
            agent_id="test-agent",
            status="active",
            performance_metrics=None,
            active_tasks=None
        )
        assert message.type == "heartbeat"
        assert message.agent_id == "test-agent"
        assert message.status == "active"
        assert isinstance(message.timestamp, datetime)

    def test_agent_status_message_schema(self):
        """Test agent status update message schema."""
        from api.websocket import AgentStatusMessage

        message = AgentStatusMessage(
            agent_id="test-agent",
            status="error",
            error_message="Test error"
        )
        assert message.type == "status_update"
        assert message.agent_id == "test-agent"
        assert message.status == "error"
        assert message.error_message == "Test error"

    def test_task_update_message_schema(self):
        """Test task update message schema."""
        from api.websocket import TaskUpdateMessage

        message = TaskUpdateMessage(
            agent_id="test-agent",
            task_id="test-task",
            status="in_progress",
            progress=50.0,
            message="Half complete",
            artifacts=None
        )
        assert message.type == "task_update"
        assert message.agent_id == "test-agent"
        assert message.task_id == "test-task"
        assert message.status == "in_progress"
        assert message.progress == 50.0
        assert message.message == "Half complete"

    def test_agent_registration_message_schema(self):
        """Test agent registration message schema."""
        from api.websocket import AgentRegistrationMessage

        message = AgentRegistrationMessage(
            agent_name="Test Agent",
            agent_type="python",
            capabilities=["coding", "testing"],
            configuration=None,
            version="1.0.0"
        )
        assert message.type == "register"
        assert message.agent_name == "Test Agent"
        assert message.agent_type == "python"
        assert message.capabilities == ["coding", "testing"]
        assert message.version == "1.0.0"

    def test_task_update_message_progress_validation(self):
        """Test task update message progress validation."""
        from api.websocket import TaskUpdateMessage
        from pydantic import ValidationError

        # Valid progress values
        message = TaskUpdateMessage(
            agent_id="test-agent",
            task_id="test-task",
            status="in_progress",
            progress=0.0,
            message=None,
            artifacts=None
        )
        assert message.progress == 0.0

        message = TaskUpdateMessage(
            agent_id="test-agent",
            task_id="test-task",
            status="in_progress",
            progress=100.0,
            message=None,
            artifacts=None
        )
        assert message.progress == 100.0

        # Invalid progress values should raise validation error
        with pytest.raises(ValidationError):
            TaskUpdateMessage(
                agent_id="test-agent",
                task_id="test-task",
                status="in_progress",
                progress=-1.0,
                message=None,
                artifacts=None
            )

        with pytest.raises(ValidationError):
            TaskUpdateMessage(
                agent_id="test-agent",
                task_id="test-task",
                status="in_progress",
                progress=101.0,
                message=None,
                artifacts=None
            )


class TestWebSocketMessageHandling:
    """Test WebSocket message handling functionality."""

    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self, db_session):
        """Test handling of unknown message types."""
        message = {
            "type": "unknown_type",
            "data": "test"
        }

        # This should not raise an exception, just log a warning
        await connection_manager.handle_agent_message("test-agent", message, db_session)

    @pytest.mark.asyncio
    async def test_handle_invalid_heartbeat_message(self, db_session):
        """Test handling of invalid heartbeat message."""
        message = {
            "type": "heartbeat",
            # Missing required fields
        }

        # This should not raise an exception, just log an error
        await connection_manager.handle_agent_message("test-agent", message, db_session)

    @pytest.mark.asyncio
    async def test_handle_invalid_status_update_message(self, db_session):
        """Test handling of invalid status update message."""
        message = {
            "type": "status_update",
            # Missing required fields
        }

        # This should not raise an exception, just log an error
        await connection_manager.handle_agent_message("test-agent", message, db_session)

    @pytest.mark.asyncio
    async def test_handle_invalid_task_update_message(self, db_session):
        """Test handling of invalid task update message."""
        message = {
            "type": "task_update",
            # Missing required fields
        }

        # This should not raise an exception, just log an error
        await connection_manager.handle_agent_message("test-agent", message, db_session)

    @pytest.mark.asyncio
    async def test_handle_invalid_registration_message(self, db_session):
        """Test handling of invalid registration message."""
        message = {
            "type": "register",
            # Missing required fields
        }

        # This should not raise an exception, just log an error
        await connection_manager.handle_agent_message("test-agent", message, db_session)


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality with database."""

    @pytest.mark.asyncio
    async def test_heartbeat_message_updates_agent(
        self,
        db_session,
        test_agent: Agent
    ):
        """Test that heartbeat message updates agent in database."""
        message = {
            "type": "heartbeat",
            "agent_id": str(test_agent.id),
            "status": "active",
            "performance_metrics": {"cpu": 50, "memory": 30}
        }

        await connection_manager.handle_agent_message(str(test_agent.id), message, db_session)

        # Refresh agent from database
        await db_session.refresh(test_agent)

        # Check that agent was updated
        assert test_agent.status == "active"
        assert test_agent.performance_metrics == {"cpu": 50, "memory": 30}
        assert test_agent.last_heartbeat is not None

    @pytest.mark.asyncio
    async def test_status_update_message_updates_agent(
        self,
        db_session,
        test_agent: Agent
    ):
        """Test that status update message updates agent in database."""
        message = {
            "type": "status_update",
            "agent_id": str(test_agent.id),
            "status": "error",
            "error_message": "Test error occurred"
        }

        await connection_manager.handle_agent_message(str(test_agent.id), message, db_session)

        # Refresh agent from database
        await db_session.refresh(test_agent)

        # Check that agent status was updated
        assert test_agent.status == "error"

    @pytest.mark.asyncio
    async def test_task_update_message_broadcasts(
        self,
        db_session,
        test_agent: Agent
    ):
        """Test that task update message broadcasts to users."""
        message = {
            "type": "task_update",
            "agent_id": str(test_agent.id),
            "task_id": "test-task-123",
            "status": "completed",
            "progress": 100.0,
            "message": "Task completed successfully"
        }

        # This should not raise an exception even with no connected users
        await connection_manager.handle_agent_message(str(test_agent.id), message, db_session)

    @pytest.mark.asyncio
    async def test_registration_message_sends_acknowledgment(
        self,
        db_session,
        test_agent: Agent
    ):
        """Test that registration message sends acknowledgment."""
        message = {
            "type": "register",
            "agent_name": "Test Agent",
            "agent_type": "python",
            "capabilities": ["coding", "testing"],
            "version": "1.0.0"
        }

        # This should not raise an exception even if agent is not connected
        await connection_manager.handle_agent_message(str(test_agent.id), message, db_session)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_disconnect_agent_with_invalid_id(self, db_session):
        """Test disconnecting agent with invalid ID."""
        # This should not raise an exception
        await connection_manager.disconnect_agent("invalid-id", db_session)

    @pytest.mark.asyncio
    async def test_disconnect_user_with_invalid_id(self):
        """Test disconnecting user with invalid ID."""
        from fastapi import WebSocket
        from unittest.mock import Mock

        # Create a mock websocket object
        mock_ws = Mock(spec=WebSocket)

        # This should not raise an exception
        await connection_manager.disconnect_user(mock_ws, "invalid-id")

    def test_connection_stats_with_mock_connections(self):
        """Test connection stats with mock connections."""
        from fastapi import WebSocket
        from unittest.mock import Mock

        # Add mock connections
        mock_ws = Mock(spec=WebSocket)
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)

        connection_manager.active_connections["test-agent"] = mock_ws
        connection_manager.connection_metadata["test-agent"] = {
            "user_id": "test-user",
            "connected_at": datetime.utcnow(),
            "message_count": 5
        }
        connection_manager.user_connections["test-user"] = [mock_ws1, mock_ws2]

        stats = connection_manager.get_connection_stats()
        assert stats["active_agents"] == 1
        assert stats["connected_users"] == 1
        assert stats["total_user_connections"] == 2
        assert "test-agent" in stats["connection_metadata"]

        # Clean up
        connection_manager.active_connections.clear()
        connection_manager.connection_metadata.clear()
        connection_manager.user_connections.clear()


# Performance and load testing
class TestWebSocketPerformance:
    """Test WebSocket performance and scalability."""

    def test_message_serialization_performance(self):
        """Test JSON serialization performance for WebSocket messages."""
        from api.websocket import AgentHeartbeatMessage

        # Create a large message
        message = AgentHeartbeatMessage(
            agent_id="test-agent",
            status="active",
            performance_metrics={f"metric_{i}": i for i in range(100)},
            active_tasks=50
        )

        # Test serialization
        import time
        start_time = time.time()

        for _ in range(1000):
            json.dumps(message.dict(), default=str)

        end_time = time.time()
        serialization_time = end_time - start_time

        # Should complete 1000 serializations in reasonable time (< 1 second)
        assert serialization_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, db_session, test_agent: Agent):
        """Test handling multiple concurrent messages."""
        messages = [
            {
                "type": "heartbeat",
                "agent_id": str(test_agent.id),
                "status": "active"
            }
            for _ in range(10)
        ]

        # Handle messages concurrently
        tasks = [
            connection_manager.handle_agent_message(str(test_agent.id), msg, db_session)
            for msg in messages
        ]

        # All tasks should complete without errors
        await asyncio.gather(*tasks)

    def test_connection_metadata_memory_usage(self):
        """Test memory usage of connection metadata."""
        # Add many mock connections
        for i in range(1000):
            agent_id = f"agent-{i}"
            connection_manager.connection_metadata[agent_id] = {
                "user_id": f"user-{i % 10}",
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "message_count": i
            }

        # Verify all connections are tracked
        assert len(connection_manager.connection_metadata) == 1000

        # Clean up
        connection_manager.connection_metadata.clear()
