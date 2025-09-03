"""
Agent Lifecycle Management

This module provides comprehensive agent lifecycle management including:
- Health check endpoints for agents
- Automatic recovery mechanisms
- Performance metrics collection
- Agent timeout handling
- Lifecycle hooks and events
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from auth.dependencies import get_current_user, require_role
from database import get_async_db, AsyncSessionLocal
from models.user import User
from models.agent import Agent
from api.schemas.agent import AgentHealthResponse, AgentMetricsResponse, AgentRecoveryResponse
from api.websocket import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agent-lifecycle"])

# Configuration constants
AGENT_TIMEOUT_MINUTES = 5
HEALTH_CHECK_INTERVAL_SECONDS = 30
MAX_RECOVERY_ATTEMPTS = 3
PERFORMANCE_METRICS_RETENTION_DAYS = 30


class AgentLifecycleManager:
    """Manages agent lifecycle operations including health checks and recovery."""

    def __init__(self):
        self.recovery_attempts: Dict[UUID, int] = {}
        self.last_health_check: Dict[UUID, datetime] = {}
        self._background_tasks_running = False

    async def start_background_tasks(self):
        """Start background tasks for agent lifecycle management."""
        if not self._background_tasks_running:
            self._background_tasks_running = True
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._cleanup_loop())
            logger.info("Agent lifecycle background tasks started")

    async def stop_background_tasks(self):
        """Stop background tasks for agent lifecycle management."""
        self._background_tasks_running = False
        logger.info("Agent lifecycle background tasks stopped")

    async def _health_check_loop(self):
        """Background task to perform periodic health checks on agents."""
        while self._background_tasks_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    async def _cleanup_loop(self):
        """Background task to clean up old metrics and recovery attempts."""
        while self._background_tasks_running:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Run cleanup every hour
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)

    async def _perform_health_checks(self):
        """Perform health checks on all active agents."""
        async with AsyncSessionLocal() as db:
            # Get all active agents
            result = await db.execute(
                select(Agent).where(
                    and_(
                        Agent.status.in_(["IDLE", "BUSY"]),
                        Agent.is_approved == True
                    )
                )
            )
            agents = result.scalars().all()

            timeout_threshold = datetime.utcnow() - timedelta(minutes=AGENT_TIMEOUT_MINUTES)

            for agent in agents:
                if agent.last_heartbeat and agent.last_heartbeat < timeout_threshold:
                    await self._handle_agent_timeout(agent, db)
                elif agent.id not in self.last_health_check:
                    self.last_health_check[agent.id] = datetime.utcnow()

    async def _handle_agent_timeout(self, agent: Agent, db: AsyncSession):
        """Handle agent timeout by attempting recovery or marking as inactive."""
        logger.warning(f"Agent {agent.id} ({agent.name}) has timed out")

        recovery_count = self.recovery_attempts.get(agent.id, 0)

        if recovery_count < MAX_RECOVERY_ATTEMPTS:
            # Attempt recovery
            self.recovery_attempts[agent.id] = recovery_count + 1
            await self._attempt_agent_recovery(agent, db)
        else:
            # Mark as inactive after max recovery attempts
            await self._mark_agent_inactive(agent, db)
            self.recovery_attempts.pop(agent.id, None)

    async def _attempt_agent_recovery(self, agent: Agent, db: AsyncSession):
        """Attempt to recover a timed-out agent."""
        logger.info(f"Attempting recovery for agent {agent.id} ({agent.name})")

        # Send recovery message via WebSocket if connected
        recovery_message = {
            "type": "recovery_request",
            "agent_id": str(agent.id),
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": self.recovery_attempts.get(agent.id, 0)
        }

        await connection_manager.send_to_agent(agent.id, recovery_message)

        # Update agent status to indicate recovery attempt
        await db.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(
                status="recovering",
                error_message=f"Recovery attempt {self.recovery_attempts.get(agent.id, 0)}",
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()

    async def _mark_agent_inactive(self, agent: Agent, db: AsyncSession):
        """Mark an agent as inactive after failed recovery attempts."""
        logger.error(f"Marking agent {agent.id} ({agent.name}) as inactive after failed recovery")

        await db.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(
                status="inactive",
                error_message="Agent timed out and recovery failed",
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()

        # Notify via WebSocket
        notification = {
            "type": "agent_inactive",
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "timeout_and_recovery_failed"
        }

        await connection_manager.broadcast_to_users(notification)

    async def _cleanup_old_data(self):
        """Clean up old performance metrics and recovery attempts."""
        cutoff_date = datetime.utcnow() - timedelta(days=PERFORMANCE_METRICS_RETENTION_DAYS)

        # Clean up old recovery attempts for inactive agents
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Agent.id).where(Agent.status == "inactive")
            )
            inactive_agent_ids = [row[0] for row in result.fetchall()]

            for agent_id in inactive_agent_ids:
                self.recovery_attempts.pop(agent_id, None)
                self.last_health_check.pop(agent_id, None)

        logger.info(f"Cleaned up lifecycle data for {len(inactive_agent_ids)} inactive agents")


# Global lifecycle manager instance
lifecycle_manager = AgentLifecycleManager()


@router.get("/{agent_id}/health", response_model=AgentHealthResponse)
async def get_agent_health(
    agent_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get health status for a specific agent."""
    # Get agent with owner information
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.owner))
        .where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permissions (owner or admin can view health)
    if current_user.role != "ADMIN" and agent.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this agent's health")

    # Calculate health metrics
    now = datetime.utcnow()
    is_healthy = True
    health_issues = []

    # Check last heartbeat
    if agent.last_heartbeat:
        time_since_heartbeat = now - agent.last_heartbeat
        if time_since_heartbeat > timedelta(minutes=AGENT_TIMEOUT_MINUTES):
            is_healthy = False
            health_issues.append(f"No heartbeat for {time_since_heartbeat.total_seconds():.0f} seconds")
    else:
        is_healthy = False
        health_issues.append("No heartbeat received")

    # Check agent status
    if agent.status in ["error", "inactive"]:
        is_healthy = False
        health_issues.append(f"Agent status: {agent.status}")

    # Check for error messages
    if agent.error_message:
        is_healthy = False
        health_issues.append(f"Error: {agent.error_message}")

    # Check WebSocket connection
    is_connected = await connection_manager.is_agent_connected(str(agent_id))
    if not is_connected and agent.status == "active":
        is_healthy = False
        health_issues.append("WebSocket connection lost")

    return AgentHealthResponse(
        agent_id=agent_id,
        is_healthy=is_healthy,
        status=agent.status,
        last_heartbeat=agent.last_heartbeat,
        last_active=agent.last_active,
        is_connected=is_connected,
        health_issues=health_issues,
        recovery_attempts=lifecycle_manager.recovery_attempts.get(agent_id, 0),
        uptime_seconds=int((now - agent.created_at).total_seconds()) if agent.created_at else 0
    )


@router.get("/{agent_id}/metrics", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    agent_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a specific agent."""
    # Get agent with owner information
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.owner))
        .where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permissions (owner or admin can view metrics)
    if current_user.role != "ADMIN" and agent.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this agent's metrics")

    # Extract performance metrics from agent data
    performance_metrics = agent.performance_metrics or {}

    # Calculate additional metrics
    now = datetime.utcnow()
    uptime_seconds = int((now - agent.created_at).total_seconds()) if agent.created_at else 0

    # Calculate availability percentage
    total_time = uptime_seconds
    downtime_seconds = performance_metrics.get("downtime_seconds", 0)
    availability_percentage = ((total_time - downtime_seconds) / total_time * 100) if total_time > 0 else 0

    return AgentMetricsResponse(
        agent_id=agent_id,
        uptime_seconds=uptime_seconds,
        total_tasks_completed=performance_metrics.get("tasks_completed", 0),
        total_tasks_failed=performance_metrics.get("tasks_failed", 0),
        average_response_time_ms=performance_metrics.get("avg_response_time_ms", 0),
        cpu_usage_percent=performance_metrics.get("cpu_usage", 0),
        memory_usage_mb=performance_metrics.get("memory_usage_mb", 0),
        availability_percentage=round(availability_percentage, 2),
        last_performance_update=agent.updated_at,
        error_rate_percentage=performance_metrics.get("error_rate", 0)
    )


@router.post("/{agent_id}/recover", response_model=AgentRecoveryResponse)
async def recover_agent(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role(["ADMIN", "DIRECTOR"]))
):
    """Manually trigger agent recovery process."""
    # Get agent
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if agent needs recovery
    if agent.status in ["IDLE", "BUSY"]:
        raise HTTPException(status_code=400, detail="Agent does not need recovery")

    # Reset recovery attempts for manual recovery
    lifecycle_manager.recovery_attempts[agent_id] = 0

    # Trigger recovery in background
    background_tasks.add_task(
        lifecycle_manager._attempt_agent_recovery,
        agent,
        db
    )

    logger.info(f"Manual recovery triggered for agent {agent_id} by user {current_user.id}")

    return AgentRecoveryResponse(
        agent_id=agent_id,
        recovery_initiated=True,
        recovery_attempt=1,
        estimated_recovery_time_seconds=30,
        message="Recovery process initiated"
    )


@router.get("/health/summary")
async def get_agents_health_summary(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role(["ADMIN", "DIRECTOR"]))
):
    """Get health summary for all agents."""
    # Get all agents
    result = await db.execute(
        select(Agent).where(Agent.is_approved == True)
    )
    agents = result.scalars().all()

    # Calculate summary statistics
    total_agents = len(agents)
    healthy_agents = 0
    unhealthy_agents = 0
    inactive_agents = 0
    recovering_agents = 0

    now = datetime.utcnow()
    timeout_threshold = now - timedelta(minutes=AGENT_TIMEOUT_MINUTES)

    for agent in agents:
        if agent.status == "inactive":
            inactive_agents += 1
        elif agent.status == "recovering":
            recovering_agents += 1
        elif agent.status in ["error"] or (agent.last_heartbeat and agent.last_heartbeat < timeout_threshold):
            unhealthy_agents += 1
        else:
            healthy_agents += 1

    return {
        "total_agents": total_agents,
        "healthy_agents": healthy_agents,
        "unhealthy_agents": unhealthy_agents,
        "inactive_agents": inactive_agents,
        "recovering_agents": recovering_agents,
        "health_check_interval_seconds": HEALTH_CHECK_INTERVAL_SECONDS,
        "agent_timeout_minutes": AGENT_TIMEOUT_MINUTES,
        "last_health_check": datetime.utcnow().isoformat()
    }


# Lifecycle hooks for application startup/shutdown
async def start_agent_lifecycle():
    """Start agent lifecycle management."""
    await lifecycle_manager.start_background_tasks()


async def stop_agent_lifecycle():
    """Stop agent lifecycle management."""
    await lifecycle_manager.stop_background_tasks()
