"""
Task Database Model

This module contains the Task model and related enums for the Overseer platform.
Handles task management, assignment, and progress tracking.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

# Association table for task dependencies (many-to-many relationship)
task_dependencies = Table(
    'task_dependencies',
    BaseModel.metadata,
    Column('task_id', UUID(as_uuid=True),
           ForeignKey('tasks.id'), primary_key=True),
    Column('dependency_id', UUID(as_uuid=True),
           ForeignKey('tasks.id'), primary_key=True)
)


class TaskStatus(enum.Enum):
    """
    Task status values.

    PENDING: Task is created but not yet assigned
    ASSIGNED: Task is assigned to an agent
    IN_PROGRESS: Task is being worked on
    COMPLETED: Task is completed successfully
    FAILED: Task failed to complete
    CANCELLED: Task was cancelled
    """
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    """
    Task priority levels.

    LOW: Low priority task
    NORMAL: Normal priority task
    HIGH: High priority task
    URGENT: Urgent priority task
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """
    Task model for work assignment and tracking.

    Fields:
        title: Task title/summary
        description: Detailed task description
        team_id: Foreign key to the team this task belongs to
        assigned_agent_id: Foreign key to the assigned agent (nullable)
        created_by_id: Foreign key to the user who created the task
        status: Current task status
        priority: Task priority level
        requirements: JSON object with task requirements
        artifacts: JSON array of task output artifacts
        error_message: Error message if task failed
        started_at: Timestamp when task was started
        completed_at: Timestamp when task was completed

    Relationships:
        team: Team this task belongs to
        assigned_agent: Agent assigned to this task
        created_by_user: User who created this task
        dependencies: Tasks this task depends on
        dependents: Tasks that depend on this task
    """
    __tablename__ = "tasks"

    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey(
        'teams.id'), nullable=True)
    assigned_agent_id = Column(
        UUID(as_uuid=True), ForeignKey('agents.id'), nullable=True)
    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey(
        'tasks.id'), nullable=True)
    status = Column(String(20), nullable=False,
                    default=TaskStatus.PENDING.value)
    priority = Column(String(10), nullable=False,
                      default=TaskPriority.NORMAL.value)
    requirements = Column(JSON, nullable=True)
    artifacts = Column(JSON, nullable=True)  # List of output artifacts
    task_metadata = Column(JSON, nullable=True)  # Additional task metadata
    error_message = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # In minutes
    actual_duration = Column(Integer, nullable=True)  # In minutes

    # Relationships
    team = relationship("Team", back_populates="tasks")
    assigned_agent = relationship("Agent", back_populates="assigned_tasks")
    created_by_user = relationship("User", back_populates="created_tasks")
    parent_task = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task")
    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin="Task.id == task_dependencies.c.task_id",
        secondaryjoin="Task.id == task_dependencies.c.dependency_id",
        back_populates="dependents"
    )
    dependents = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin="Task.id == task_dependencies.c.dependency_id",
        secondaryjoin="Task.id == task_dependencies.c.task_id",
        back_populates="dependencies"
    )

    def __repr__(self):
        return f"<Task(title='{self.title}', status='{self.status}', priority='{self.priority}')>"

    def is_active(self) -> bool:
        """
        Check if task is in an active state.

        Returns:
            bool: True if task is pending, assigned, or in progress
        """
        return self.status in [
            TaskStatus.PENDING.value,
            TaskStatus.ASSIGNED.value,
            TaskStatus.IN_PROGRESS.value
        ]

    def is_completed(self) -> bool:
        """
        Check if task is completed (successfully or failed).

        Returns:
            bool: True if task is completed, failed, or cancelled
        """
        return self.status in [
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value
        ]

    def can_be_assigned(self) -> bool:
        """
        Check if task can be assigned to an agent.

        Returns:
            bool: True if task is in pending status
        """
        return self.status == TaskStatus.PENDING.value

    def assign_to_agent(self, agent):
        """
        Assign task to an agent.

        Args:
            agent: Agent instance to assign the task to
        """
        if self.can_be_assigned():
            self.assigned_agent_id = agent.id
            self.status = TaskStatus.ASSIGNED.value

    def start_task(self):
        """
        Mark task as started.
        """
        if self.status == TaskStatus.ASSIGNED.value:
            self.status = TaskStatus.IN_PROGRESS.value
            from sqlalchemy.sql import func
            self.started_at = func.now()

    def complete_task(self, artifacts: list = None):
        """
        Mark task as completed.

        Args:
            artifacts: Optional list of output artifacts
        """
        if self.status == TaskStatus.IN_PROGRESS.value:
            self.status = TaskStatus.COMPLETED.value
            from sqlalchemy.sql import func
            self.completed_at = func.now()
            if artifacts:
                self.artifacts = artifacts

    def fail_task(self, error_message: str):
        """
        Mark task as failed.

        Args:
            error_message: Error message describing the failure
        """
        if self.status in [TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value]:
            self.status = TaskStatus.FAILED.value
            self.error_message = error_message
            from sqlalchemy.sql import func
            self.completed_at = func.now()

    def cancel_task(self):
        """
        Cancel the task.
        """
        if self.is_active():
            self.status = TaskStatus.CANCELLED.value
            from sqlalchemy.sql import func
            self.completed_at = func.now()

    def get_priority_weight(self) -> int:
        """
        Get numeric weight for priority sorting.

        Returns:
            int: Priority weight (higher = more urgent)
        """
        priority_weights = {
            TaskPriority.LOW.value: 1,
            TaskPriority.NORMAL.value: 2,
            TaskPriority.HIGH.value: 3,
            TaskPriority.URGENT.value: 4
        }
        return priority_weights.get(self.priority, 2)

    def add_artifact(self, artifact: str):
        """
        Add an artifact to the task.

        Args:
            artifact: Artifact string to add
        """
        if self.artifacts is None:
            self.artifacts = []
        if artifact not in self.artifacts:
            self.artifacts.append(artifact)

    def set_requirement(self, key: str, value):
        """
        Set a task requirement.

        Args:
            key: Requirement key
            value: Requirement value
        """
        if self.requirements is None:
            self.requirements = {}
        self.requirements[key] = value

    def get_requirement(self, key: str, default=None):
        """
        Get a task requirement.

        Args:
            key: Requirement key
            default: Default value if key not found

        Returns:
            Requirement value or default
        """
        if self.requirements is None:
            return default
        return self.requirements.get(key, default)
