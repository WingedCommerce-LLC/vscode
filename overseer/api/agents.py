"""
Agent Management API

This module provides API endpoints for managing AI agents in the Overseer platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime

from database import get_async_db
from models.agent import Agent, AgentStatus, AgentType
from models.user import User, UserRole
from models.team import Team
from auth.dependencies import get_current_user, require_role
from api.schemas.agent import (
    AgentRegistrationRequest,
    AgentUpdateRequest,
    AgentStatusUpdateRequest,
    AgentHeartbeatRequest,
    AgentResponse,
    AgentListResponse,
    AgentApprovalRequest,
    AgentSearchRequest,
    AgentStatsResponse,
    AgentStatusEnum,
    AgentTypeEnum
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_data: AgentRegistrationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new AI agent.

    Requires authentication. The current user becomes the owner of the agent.
    Agents require approval from an admin or director before they can be used.
    """
    # Check if agent name already exists for this user
    existing_agent = await db.execute(
        select(Agent).where(
            and_(
                Agent.name == agent_data.name,
                Agent.owner_id == current_user.id
            )
        )
    )
    if existing_agent.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent with this name already exists"
        )

    # Validate team assignment if provided
    if agent_data.team_id:
        team_result = await db.execute(
            select(Team).options(selectinload(Team.members)).where(Team.id == agent_data.team_id)
        )
        team = team_result.scalar_one_or_none()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Check if user has access to assign agents to this team
        # Users can assign their own agents to any active team
        # Only admins/directors can assign agents to inactive teams
        if team.is_active is False and current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to assign agents to inactive teams"
            )

    # Create the agent
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        type=agent_data.type.value,
        team_id=agent_data.team_id,
        owner_id=current_user.id,
        capabilities=agent_data.capabilities,
        configuration=agent_data.configuration.model_dump() if agent_data.configuration else None,
        version=agent_data.version,
        status=AgentStatus.INACTIVE.value,
        is_approved=current_user.role == UserRole.ADMIN  # Auto-approve for admins
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return agent


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[AgentTypeEnum] = Query(None, description="Filter by agent type"),
    status: Optional[AgentStatusEnum] = Query(None, description="Filter by agent status"),
    team_id: Optional[uuid.UUID] = Query(None, description="Filter by team ID"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    query: Optional[str] = Query(None, max_length=100, description="Search query"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    List agents with filtering and pagination.

    Users can see:
    - Their own agents
    - Agents in teams they belong to
    - All agents (if admin/director)
    """
    # Build base query
    stmt = select(Agent).options(selectinload(Agent.team))

    # Apply access control
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        # Regular users can only see their own agents or agents in their teams
        user_teams_subq = select(Team.id).join(Team.members).where(Team.members.any(User.id == current_user.id))
        stmt = stmt.where(
            or_(
                Agent.owner_id == current_user.id,
                Agent.team_id.in_(user_teams_subq)
            )
        )

    # Apply filters
    if type:
        stmt = stmt.where(Agent.type == type.value)
    if status:
        stmt = stmt.where(Agent.status == status.value)
    if team_id:
        stmt = stmt.where(Agent.team_id == team_id)
    if is_approved is not None:
        stmt = stmt.where(Agent.is_approved == is_approved)
    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                Agent.name.ilike(search_term),
                Agent.description.ilike(search_term)
            )
        )

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page).order_by(Agent.created_at.desc())

    # Execute query
    result = await db.execute(stmt)
    agents = result.scalars().all()

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page

    return AgentListResponse(
        agents=list(agents),
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific agent by ID."""
    stmt = select(Agent).options(selectinload(Agent.team)).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        if agent.owner_id != current_user.id:
            # Check if user is in the same team
            if not agent.team or current_user not in agent.team.members:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this agent"
                )

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    agent_data: AgentUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update an agent's information."""
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check permissions - only owner or admin/director can update
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        if agent.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent"
            )

    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "configuration" and value:
            setattr(agent, field, value.model_dump())
        elif field == "type" and value:
            setattr(agent, field, value.value)
        else:
            setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check permissions - only owner or admin can delete
    if current_user.role != UserRole.ADMIN and agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this agent"
        )

    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/approve", response_model=AgentResponse)
async def approve_agent(
    agent_id: uuid.UUID,
    approval_data: AgentApprovalRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DIRECTOR]))
):
    """Approve or reject an agent."""
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Store original capabilities for response
    original_capabilities = agent.capabilities

    # Handle capabilities list serialization for SQLAlchemy change tracking
    if isinstance(agent.capabilities, list):
        import json
        agent.capabilities = json.dumps(agent.capabilities)

    agent.is_approved = approval_data.approved

    await db.commit()
    await db.refresh(agent)

    # Restore capabilities as list for response serialization
    if isinstance(agent.capabilities, str):
        try:
            import json
            agent.capabilities = json.loads(agent.capabilities)
        except (json.JSONDecodeError, TypeError):
            agent.capabilities = original_capabilities

    return agent


@router.post("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: uuid.UUID,
    status_data: AgentStatusUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update an agent's status."""
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check permissions - only owner or admin/director can update status
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        if agent.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent's status"
            )

    # Update status
    agent.status = status_data.status.value
    agent.error_message = status_data.error_message
    agent.last_active = datetime.utcnow()

    await db.commit()
    await db.refresh(agent)

    return agent


@router.post("/{agent_id}/heartbeat", response_model=dict)
async def agent_heartbeat(
    agent_id: uuid.UUID,
    heartbeat_data: AgentHeartbeatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Record an agent heartbeat."""
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check permissions - only owner can send heartbeats
    if agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to send heartbeats for this agent"
        )

    # Update heartbeat info
    agent.last_heartbeat = datetime.utcnow()
    if heartbeat_data.status:
        agent.status = heartbeat_data.status.value
        agent.last_active = datetime.utcnow()
    if heartbeat_data.performance_metrics:
        agent.performance_metrics = heartbeat_data.performance_metrics

    await db.commit()

    return {"message": "Heartbeat recorded", "timestamp": agent.last_heartbeat}


@router.get("/stats/overview", response_model=AgentStatsResponse)
async def get_agent_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DIRECTOR]))
):
    """Get agent statistics overview."""
    # Base query for accessible agents
    base_stmt = select(Agent)

    # Get total counts by status
    status_counts = {}
    for status_enum in AgentStatus:
        count_stmt = select(func.count()).where(Agent.status == status_enum.value)
        result = await db.execute(count_stmt)
        status_counts[status_enum.value] = result.scalar()

    # Get counts by type
    type_counts = {}
    for type_enum in AgentType:
        count_stmt = select(func.count()).where(Agent.type == type_enum.value)
        result = await db.execute(count_stmt)
        type_counts[type_enum.value] = result.scalar()

    # Get counts by team
    team_counts_stmt = select(
        Team.name,
        func.count(Agent.id).label('count')
    ).select_from(
        Team
    ).outerjoin(Agent).group_by(Team.id, Team.name)

    team_result = await db.execute(team_counts_stmt)
    team_counts = {row.name: row.count for row in team_result}

    # Get approval counts
    approved_stmt = select(func.count()).where(Agent.is_approved == True)
    pending_stmt = select(func.count()).where(Agent.is_approved == False)

    approved_result = await db.execute(approved_stmt)
    pending_result = await db.execute(pending_stmt)

    return AgentStatsResponse(
        total_agents=sum(status_counts.values()),
        active_agents=status_counts.get('active', 0),
        inactive_agents=status_counts.get('inactive', 0),
        busy_agents=status_counts.get('busy', 0),
        error_agents=status_counts.get('error', 0),
        maintenance_agents=status_counts.get('maintenance', 0),
        approved_agents=approved_result.scalar(),
        pending_approval=pending_result.scalar(),
        by_type=type_counts,
        by_team=team_counts
    )
