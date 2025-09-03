"""
Agent Database Model

This module contains the Agent model and related enums for the Overseer platform.
Handles AI agent registration, configuration, and status tracking.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


# Database-agnostic enum implementation
def create_enum_column(enum_class, column_name=None, **kwargs):
    """
    Create a database-agnostic enum column that works with both PostgreSQL and SQLite.

    For PostgreSQL: Uses native ENUM type with enum values
    For SQLite: Uses String type with enum values
    """
    # Use String type for compatibility - the migration will handle PostgreSQL enum creation
    return Column(column_name or enum_class.__name__.lower(), String(20), **kwargs)


class AgentStatus(enum.Enum):
    """
    Agent status values (matching API schema).

    INACTIVE: Agent is registered but not active
    ACTIVE: Agent is active and available
    BUSY: Agent is currently working on a task
    ERROR: Agent has encountered an error
    MAINTENANCE: Agent is in maintenance mode
    """
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentType(enum.Enum):
    """
    Agent type classifications (matching API schema).

    CODER: Code generation and modification agent
    REVIEWER: Code review and analysis agent
    TESTER: Testing and QA agent
    DOCUMENTER: Documentation agent
    ANALYST: Data analysis and reporting agent
    GENERAL: General purpose agent
    """
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    ANALYST = "analyst"
    GENERAL = "general"


class Agent(BaseModel):
    """
    Agent model for AI agent management.

    Fields:
        name: Human-readable agent name
        type: Agent type classification
        team_id: Foreign key to the team this agent belongs to
        status: Current agent status
        configuration: JSON configuration for the agent
        capabilities: List of agent capabilities
        last_heartbeat: Timestamp of last heartbeat
        error_message: Last error message if status is ERROR

    Relationships:
        team: Team this agent belongs to
        assigned_tasks: Tasks assigned to this agent
    """
    __tablename__ = "agents"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column("agent_type", String(20), nullable=False,
                  default=AgentType.GENERAL.value)
    team_id = Column(UUID(as_uuid=True), ForeignKey(
        'teams.id'), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey(
        'users.id'), nullable=False)
    status = Column(String(20), nullable=False,
                    default=AgentStatus.INACTIVE.value)
    configuration = Column(JSON, nullable=True)
    capabilities = Column(JSON, nullable=True)  # List of capability strings
    performance_metrics = Column(JSON, nullable=True)  # Performance data
    last_active = Column(DateTime(timezone=True), nullable=True)
    is_approved = Column(Boolean, nullable=False, default=False)
    version = Column(String(20), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="agents")
    owner = relationship("User", foreign_keys=[owner_id])
    assigned_tasks = relationship("Task", back_populates="assigned_agent")

    def __repr__(self):
        return f"<Agent(name='{self.name}', type='{self.type}', status='{self.status}')>"

    def is_available(self) -> bool:
        """
        Check if agent is available for new tasks.

        Returns:
            bool: True if agent can accept new tasks
        """
        return self.status == AgentStatus.INACTIVE.value

    def is_healthy(self) -> bool:
        """
        Check if agent is in a healthy state.

        Returns:
            bool: True if agent is not in error or maintenance
        """
        return self.status not in [AgentStatus.ERROR.value, AgentStatus.MAINTENANCE.value]

    def set_status(self, status: AgentStatus, error_message: str | None = None):
        """
        Update agent status.

        Args:
            status: New agent status
            error_message: Optional error message for ERROR status (not stored in DB)
        """
        self.status = status.value
        # Note: error_message is not stored in database schema

    def add_capability(self, capability: str):
        """
        Add a capability to the agent.

        Args:
            capability: Capability string to add
        """
        if self.capabilities is None:
            self.capabilities = []
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def remove_capability(self, capability: str):
        """
        Remove a capability from the agent.

        Args:
            capability: Capability string to remove
        """
        if self.capabilities and capability in self.capabilities:
            self.capabilities.remove(capability)

    def has_capability(self, capability: str) -> bool:
        """
        Check if agent has a specific capability.

        Args:
            capability: Capability string to check

        Returns:
            bool: True if agent has the capability
        """
        return self.capabilities is not None and capability in self.capabilities

    def get_active_task_count(self) -> int:
        """
        Get the number of active tasks assigned to this agent.

        Returns:
            int: Number of active tasks
        """
        from .task import TaskStatus
        return len([task for task in self.assigned_tasks
                   if task.status not in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]])
