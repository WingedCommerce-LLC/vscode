"""
Agent API Schemas

This module contains Pydantic schemas for agent-related API operations.
"""

from pydantic import BaseModel, Field, validator, field_validator, model_validator, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

from models.agent import AgentStatus, AgentType


class AgentStatusEnum(str, Enum):
    """Agent status enum for API."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentTypeEnum(str, Enum):
    """Agent type enum for API."""
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    ANALYST = "analyst"
    GENERAL = "general"


class AgentCapability(BaseModel):
    """Schema for agent capability."""
    name: str = Field(..., description="Capability name")
    description: Optional[str] = Field(None, description="Capability description")
    version: Optional[str] = Field(None, description="Capability version")


class AgentConfiguration(BaseModel):
    """Schema for agent configuration."""
    max_concurrent_tasks: int = Field(1, ge=1, le=10, description="Maximum concurrent tasks")
    timeout_seconds: int = Field(300, ge=30, le=3600, description="Task timeout in seconds")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration settings")


class AgentRegistrationRequest(BaseModel):
    """Schema for agent registration request."""
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    type: AgentTypeEnum = Field(AgentTypeEnum.GENERAL, description="Agent type")
    team_id: Optional[uuid.UUID] = Field(None, description="Team ID to assign agent to")
    capabilities: Optional[List[str]] = Field(default_factory=list, description="List of agent capabilities")
    configuration: Optional[AgentConfiguration] = Field(default_factory=lambda: AgentConfiguration(), description="Agent configuration")
    version: Optional[str] = Field(None, max_length=20, description="Agent version")

    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Validate capabilities list."""
        if v is None:
            return []
        # Remove duplicates and empty strings while preserving order
        seen = set()
        result = []
        for cap in v:
            if cap and cap.strip() and cap.strip() not in seen:
                cleaned_cap = cap.strip()
                seen.add(cleaned_cap)
                result.append(cleaned_cap)
        return result

    @validator('name')
    def validate_name(cls, v):
        """Validate agent name."""
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()


class AgentUpdateRequest(BaseModel):
    """Schema for agent update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    type: Optional[AgentTypeEnum] = Field(None, description="Agent type")
    team_id: Optional[uuid.UUID] = Field(None, description="Team ID to assign agent to")
    capabilities: Optional[List[str]] = Field(None, description="List of agent capabilities")
    configuration: Optional[AgentConfiguration] = Field(None, description="Agent configuration")
    version: Optional[str] = Field(None, max_length=20, description="Agent version")

    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Validate capabilities list."""
        if v is None:
            return None
        # Remove duplicates and empty strings while preserving order
        seen = set()
        result = []
        for cap in v:
            if cap and cap.strip() and cap.strip() not in seen:
                cleaned_cap = cap.strip()
                seen.add(cleaned_cap)
                result.append(cleaned_cap)
        return result

    @validator('name')
    def validate_name(cls, v):
        """Validate agent name."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Agent name cannot be empty')
        return v.strip() if v else None


class AgentStatusUpdateRequest(BaseModel):
    """Schema for agent status update request."""
    status: AgentStatusEnum = Field(..., description="New agent status")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if status is ERROR")

    @model_validator(mode='after')
    def validate_error_message_required(self):
        """Validate error message is provided when status is ERROR."""
        if self.status == AgentStatusEnum.ERROR and not self.error_message:
            raise ValueError('Error message is required when status is ERROR')
        return self


class AgentHeartbeatRequest(BaseModel):
    """Schema for agent heartbeat request."""
    status: Optional[AgentStatusEnum] = Field(None, description="Current agent status")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    active_tasks: Optional[int] = Field(None, ge=0, description="Number of active tasks")


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: uuid.UUID = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    type: str = Field(..., description="Agent type")
    team_id: Optional[uuid.UUID] = Field(None, description="Team ID")
    owner_id: uuid.UUID = Field(..., description="Owner user ID")
    status: str = Field(..., description="Agent status")
    capabilities: Optional[List[str]] = Field(None, description="Agent capabilities")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    last_active: Optional[datetime] = Field(None, description="Last active timestamp")
    error_message: Optional[str] = Field(None, description="Error message if status is ERROR")
    is_approved: bool = Field(..., description="Whether agent is approved")
    version: Optional[str] = Field(None, description="Agent version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for agent list response."""
    agents: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


class AgentApprovalRequest(BaseModel):
    """Schema for agent approval request."""
    approved: bool = Field(..., description="Whether to approve or reject the agent")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for approval/rejection")


class AgentSearchRequest(BaseModel):
    """Schema for agent search request."""
    query: Optional[str] = Field(None, max_length=100, description="Search query")
    type: Optional[AgentTypeEnum] = Field(None, description="Filter by agent type")
    status: Optional[AgentStatusEnum] = Field(None, description="Filter by agent status")
    team_id: Optional[uuid.UUID] = Field(None, description="Filter by team ID")
    capabilities: Optional[List[str]] = Field(None, description="Filter by capabilities")
    is_approved: Optional[bool] = Field(None, description="Filter by approval status")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class AgentStatsResponse(BaseModel):
    """Schema for agent statistics response."""
    total_agents: int = Field(..., description="Total number of agents")
    active_agents: int = Field(..., description="Number of active agents")
    inactive_agents: int = Field(..., description="Number of inactive agents")
    busy_agents: int = Field(..., description="Number of busy agents")
    error_agents: int = Field(..., description="Number of agents in error state")
    maintenance_agents: int = Field(..., description="Number of agents in maintenance")
    approved_agents: int = Field(..., description="Number of approved agents")
    pending_approval: int = Field(..., description="Number of agents pending approval")
    by_type: Dict[str, int] = Field(..., description="Agent count by type")
    by_team: Dict[str, int] = Field(..., description="Agent count by team")


class AgentHealthResponse(BaseModel):
    """Schema for agent health response."""
    agent_id: uuid.UUID = Field(..., description="Agent ID")
    is_healthy: bool = Field(..., description="Whether the agent is healthy")
    status: str = Field(..., description="Current agent status")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    last_active: Optional[datetime] = Field(None, description="Last active timestamp")
    is_connected: bool = Field(..., description="Whether agent is connected via WebSocket")
    health_issues: List[str] = Field(default_factory=list, description="List of health issues")
    recovery_attempts: int = Field(0, description="Number of recovery attempts")
    uptime_seconds: int = Field(0, description="Agent uptime in seconds")


class AgentMetricsResponse(BaseModel):
    """Schema for agent performance metrics response."""
    agent_id: uuid.UUID = Field(..., description="Agent ID")
    uptime_seconds: int = Field(..., description="Agent uptime in seconds")
    total_tasks_completed: int = Field(0, description="Total tasks completed")
    total_tasks_failed: int = Field(0, description="Total tasks failed")
    average_response_time_ms: float = Field(0.0, description="Average response time in milliseconds")
    cpu_usage_percent: float = Field(0.0, description="CPU usage percentage")
    memory_usage_mb: float = Field(0.0, description="Memory usage in MB")
    availability_percentage: float = Field(0.0, description="Availability percentage")
    last_performance_update: Optional[datetime] = Field(None, description="Last performance update timestamp")
    error_rate_percentage: float = Field(0.0, description="Error rate percentage")


class AgentRecoveryResponse(BaseModel):
    """Schema for agent recovery response."""
    agent_id: uuid.UUID = Field(..., description="Agent ID")
    recovery_initiated: bool = Field(..., description="Whether recovery was initiated")
    recovery_attempt: int = Field(..., description="Recovery attempt number")
    estimated_recovery_time_seconds: int = Field(..., description="Estimated recovery time in seconds")
    message: str = Field(..., description="Recovery status message")
