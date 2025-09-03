"""
WebSocket Connection Manager for Agent Communication

This module provides WebSocket connection management for real-time communication
between the Overseer platform and AI agents.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ValidationError

from database import get_async_db
from auth.websocket_auth import get_current_user_websocket
from models.user import User
from models.agent import Agent
from api.logging_config import get_logger

logger = get_logger(__name__)

# WebSocket Message Schemas
class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""
    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Message correlation ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")


class AgentHeartbeatMessage(BaseModel):
    """Agent heartbeat message schema."""
    type: str = Field(default="heartbeat", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Agent status")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    active_tasks: Optional[int] = Field(None, description="Number of active tasks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Heartbeat timestamp")


class AgentStatusMessage(BaseModel):
    """Agent status update message schema."""
    type: str = Field(default="status_update", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="New agent status")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status update timestamp")


class TaskUpdateMessage(BaseModel):
    """Task update message schema."""
    type: str = Field(default="task_update", description="Message type")
    agent_id: str = Field(..., description="Agent ID")
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Task progress percentage")
    message: Optional[str] = Field(None, description="Progress message")
    artifacts: Optional[List[str]] = Field(None, description="Task artifacts")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")


class AgentRegistrationMessage(BaseModel):
    """Agent registration via WebSocket message schema."""
    type: str = Field(default="register", description="Message type")
    agent_name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    version: Optional[str] = Field(None, description="Agent version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")


class ConnectionManager:
    """WebSocket connection manager for agent communication."""

    def __init__(self):
        # Active connections: {agent_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection metadata: {agent_id: connection_info}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # User connections: {user_id: List[WebSocket]}
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect_agent(
        self,
        websocket: WebSocket,
        agent_id: str,
        user: User,
        db: AsyncSession
    ):
        """Connect an agent via WebSocket."""
        try:
            await websocket.accept()

            # Verify agent exists and user has permission
            agent = await db.get(Agent, agent_id)
            if not agent:
                await websocket.close(code=4004, reason="Agent not found")
                return False

            if agent.owner_id != user.id and user.role not in ["admin", "director"]:
                await websocket.close(code=4003, reason="Insufficient permissions")
                return False

            # Store connection
            self.active_connections[agent_id] = websocket
            self.connection_metadata[agent_id] = {
                "user_id": str(user.id),
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "message_count": 0
            }

            # Update agent status to active
            agent.status = "active"
            agent.last_heartbeat = datetime.utcnow()
            db.add(agent)
            await db.commit()

            logger.info(f"Agent {agent_id} connected via WebSocket", extra={
                "agent_id": agent_id,
                "user_id": str(user.id),
                "agent_name": agent.name
            })

            return True

        except Exception as e:
            logger.error(f"Failed to connect agent {agent_id}: {str(e)}", extra={
                "agent_id": agent_id,
                "error": str(e)
            })
            await websocket.close(code=4000, reason="Connection failed")
            return False

    async def connect_user(self, websocket: WebSocket, user: User):
        """Connect a user for monitoring agents."""
        try:
            await websocket.accept()

            user_id = str(user.id)
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []

            self.user_connections[user_id].append(websocket)

            logger.info(f"User {user_id} connected for monitoring", extra={
                "user_id": user_id,
                "username": user.username
            })

            return True

        except Exception as e:
            logger.error(f"Failed to connect user {user.id}: {str(e)}", extra={
                "user_id": str(user.id),
                "error": str(e)
            })
            await websocket.close(code=4000, reason="Connection failed")
            return False

    async def disconnect_agent(self, agent_id: str, db: AsyncSession):
        """Disconnect an agent."""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]

            try:
                await websocket.close()
            except:
                pass  # Connection might already be closed

            # Update agent status
            try:
                agent = await db.get(Agent, agent_id)
                if agent:
                    agent.status = "inactive"
                    db.add(agent)
                    await db.commit()
            except Exception as e:
                logger.error(f"Failed to update agent status on disconnect: {str(e)}")

            # Clean up
            del self.active_connections[agent_id]
            if agent_id in self.connection_metadata:
                del self.connection_metadata[agent_id]

            logger.info(f"Agent {agent_id} disconnected", extra={"agent_id": agent_id})

    async def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Disconnect a user."""
        if user_id in self.user_connections:
            try:
                self.user_connections[user_id].remove(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            except ValueError:
                pass  # WebSocket not in list

            logger.info(f"User {user_id} disconnected from monitoring", extra={"user_id": user_id})

    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Send a message to a specific agent."""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            try:
                await websocket.send_text(json.dumps(message, default=str))

                # Update message count
                if agent_id in self.connection_metadata:
                    self.connection_metadata[agent_id]["message_count"] += 1

                return True
            except Exception as e:
                logger.error(f"Failed to send message to agent {agent_id}: {str(e)}")
                # Note: Cannot disconnect agent here without db session
                # Remove from active connections for now
                if agent_id in self.active_connections:
                    del self.active_connections[agent_id]
                if agent_id in self.connection_metadata:
                    del self.connection_metadata[agent_id]
                return False
        return False

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections of a specific user."""
        if user_id in self.user_connections:
            disconnected = []
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {str(e)}")
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                await self.disconnect_user(ws, user_id)

    async def broadcast_to_users(self, message: Dict[str, Any], user_filter=None):
        """Broadcast a message to all connected users or filtered users."""
        for user_id, websockets in self.user_connections.items():
            if user_filter and not user_filter(user_id):
                continue

            await self.send_to_user(user_id, message)

    async def handle_agent_message(
        self,
        agent_id: str,
        message: Dict[str, Any],
        db: AsyncSession
    ):
        """Handle incoming message from an agent."""
        try:
            message_type = message.get("type")

            if message_type == "heartbeat":
                await self._handle_heartbeat(agent_id, message, db)
            elif message_type == "status_update":
                await self._handle_status_update(agent_id, message, db)
            elif message_type == "task_update":
                await self._handle_task_update(agent_id, message, db)
            elif message_type == "register":
                await self._handle_registration(agent_id, message, db)
            else:
                logger.warning(f"Unknown message type from agent {agent_id}: {message_type}")

        except Exception as e:
            logger.error(f"Error handling message from agent {agent_id}: {str(e)}", extra={
                "agent_id": agent_id,
                "message": message,
                "error": str(e)
            })

    async def _handle_heartbeat(self, agent_id: str, message: Dict[str, Any], db: AsyncSession):
        """Handle agent heartbeat message."""
        try:
            heartbeat = AgentHeartbeatMessage(**message)

            # Update agent in database
            agent = await db.get(Agent, agent_id)
            if agent:
                # Use update() method for proper SQLAlchemy column assignment
                from sqlalchemy import update
                stmt = update(Agent).where(Agent.id == agent_id).values(
                    last_heartbeat=datetime.utcnow(),
                    status=heartbeat.status if heartbeat.status else agent.status,
                    performance_metrics=heartbeat.performance_metrics if heartbeat.performance_metrics else agent.performance_metrics
                )
                await db.execute(stmt)
                await db.commit()

            # Update connection metadata
            if agent_id in self.connection_metadata:
                self.connection_metadata[agent_id]["last_heartbeat"] = datetime.utcnow()

            # Broadcast to monitoring users
            await self.broadcast_to_users({
                "type": "agent_heartbeat",
                "agent_id": agent_id,
                "status": heartbeat.status,
                "timestamp": heartbeat.timestamp.isoformat()
            })

        except ValidationError as e:
            logger.error(f"Invalid heartbeat message from agent {agent_id}: {str(e)}")

    async def _handle_status_update(self, agent_id: str, message: Dict[str, Any], db: AsyncSession):
        """Handle agent status update message."""
        try:
            status_update = AgentStatusMessage(**message)

            # Update agent in database
            agent = await db.get(Agent, agent_id)
            if agent:
                # Use update() method for proper SQLAlchemy column assignment
                from sqlalchemy import update
                stmt = update(Agent).where(Agent.id == agent_id).values(
                    status=status_update.status
                )
                await db.execute(stmt)
                await db.commit()

            # Broadcast to monitoring users
            await self.broadcast_to_users({
                "type": "agent_status_update",
                "agent_id": agent_id,
                "status": status_update.status,
                "error_message": status_update.error_message,
                "timestamp": status_update.timestamp.isoformat()
            })

        except ValidationError as e:
            logger.error(f"Invalid status update message from agent {agent_id}: {str(e)}")

    async def _handle_task_update(self, agent_id: str, message: Dict[str, Any], db: AsyncSession):
        """Handle task update message."""
        try:
            task_update = TaskUpdateMessage(**message)

            # Broadcast to monitoring users
            await self.broadcast_to_users({
                "type": "task_update",
                "agent_id": agent_id,
                "task_id": task_update.task_id,
                "status": task_update.status,
                "progress": task_update.progress,
                "message": task_update.message,
                "timestamp": task_update.timestamp.isoformat()
            })

        except ValidationError as e:
            logger.error(f"Invalid task update message from agent {agent_id}: {str(e)}")

    async def _handle_registration(self, agent_id: str, message: Dict[str, Any], db: AsyncSession):
        """Handle agent registration message."""
        try:
            registration = AgentRegistrationMessage(**message)

            # This would typically create a new agent or update existing one
            # For now, just acknowledge the registration
            await self.send_to_agent(agent_id, {
                "type": "registration_ack",
                "status": "acknowledged",
                "timestamp": datetime.utcnow().isoformat()
            })

        except ValidationError as e:
            logger.error(f"Invalid registration message from agent {agent_id}: {str(e)}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_agents": len(self.active_connections),
            "connected_users": len(self.user_connections),
            "total_user_connections": sum(len(conns) for conns in self.user_connections.values()),
            "connection_metadata": self.connection_metadata
        }


# Global connection manager instance
connection_manager = ConnectionManager()

# WebSocket router
router = APIRouter()


@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """WebSocket endpoint for agent connections."""
    user = None
    try:
        # Get user from WebSocket (this will need to be implemented)
        user = await get_current_user_websocket(websocket, db)

        # Connect agent
        connected = await connection_manager.connect_agent(websocket, agent_id, user, db)
        if not connected:
            return

        # Handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_agent_message(agent_id, message, db)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from agent {agent_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error in agent WebSocket {agent_id}: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error for agent {agent_id}: {str(e)}")
    finally:
        await connection_manager.disconnect_agent(agent_id, db)


@router.websocket("/ws/monitor")
async def websocket_monitor_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db)
):
    """WebSocket endpoint for user monitoring connections."""
    user = None
    try:
        # Get user from WebSocket
        user = await get_current_user_websocket(websocket, db)

        # Connect user
        connected = await connection_manager.connect_user(websocket, user)
        if not connected:
            return

        # Send initial connection stats
        await websocket.send_text(json.dumps({
            "type": "connection_stats",
            "data": connection_manager.get_connection_stats()
        }))

        # Keep connection alive and handle any incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle any monitoring commands here

            except WebSocketDisconnect:
                break
            except Exception as e:
                user_id = str(user.id) if user else "unknown"
                logger.error(f"Error in monitor WebSocket for user {user_id}: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket monitor connection error: {str(e)}")
    finally:
        if user is not None:
            await connection_manager.disconnect_user(websocket, str(user.id))
        else:
            # Close websocket if user authentication failed
            try:
                await websocket.close()
            except:
                pass
