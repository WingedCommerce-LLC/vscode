"""
Team Database Model

This module contains the Team model and association tables for the Overseer platform.
Handles team management, member relationships, and agent assignments.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Table, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

# Association table for team members (many-to-many relationship)
team_members = Table(
    'team_members',
    BaseModel.metadata,
    Column('team_id', UUID(as_uuid=True),
           ForeignKey('teams.id'), primary_key=True),
    Column('user_id', UUID(as_uuid=True),
           ForeignKey('users.id'), primary_key=True)
)


class Team(BaseModel):
    """
    Team model for organizing users and agents.

    Fields:
        name: Team name (must be unique per owner)
        description: Optional team description
        owner_id: Foreign key to the user who owns this team

    Relationships:
        owner: User who owns this team
        members: Users who are members of this team
        agents: AI agents assigned to this team
        tasks: Tasks assigned to this team
    """
    __tablename__ = "teams"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey(
        'users.id'), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship(
        "User",
        secondary=team_members,
        back_populates="team_memberships"
    )
    agents = relationship("Agent", back_populates="team",
                          cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(name='{self.name}', owner_id='{self.owner_id}')>"

    def add_member(self, user):
        """
        Add a user to this team.

        Args:
            user: User instance to add to the team
        """
        if user not in self.members:
            self.members.append(user)

    def remove_member(self, user):
        """
        Remove a user from this team.

        Args:
            user: User instance to remove from the team
        """
        if user in self.members:
            self.members.remove(user)

    def is_member(self, user) -> bool:
        """
        Check if a user is a member of this team.

        Args:
            user: User instance to check

        Returns:
            bool: True if user is a member or owner
        """
        return user == self.owner or user in self.members

    def get_member_count(self) -> int:
        """
        Get the total number of members (including owner).

        Returns:
            int: Total member count
        """
        return len(self.members) + 1  # +1 for owner

    def get_agent_count(self) -> int:
        """
        Get the number of agents assigned to this team.

        Returns:
            int: Number of agents
        """
        return len(self.agents)

    def get_active_task_count(self) -> int:
        """
        Get the number of active tasks for this team.

        Returns:
            int: Number of active tasks
        """
        from .task import TaskStatus
        return len([task for task in self.tasks if task.status != TaskStatus.COMPLETED])
