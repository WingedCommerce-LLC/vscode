"""
User Database Model

This module contains the User model and related enums for the Overseer platform.
Handles user authentication, roles, and team relationships.
"""

from sqlalchemy import Column, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class UserRole(enum.Enum):
    """
    User roles in the Overseer platform.

    ADMIN: Full system access, user management
    DIRECTOR: Team management, agent configuration
    MEMBER: Read-only access to assigned teams
    AGENT: Limited API access for task updates
    """
    ADMIN = "admin"
    DIRECTOR = "director"
    MEMBER = "member"
    AGENT = "agent"


class User(BaseModel):
    """
    User model for authentication and authorization.

    Fields:
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password for authentication
        role: User role determining permissions

    Relationships:
        owned_teams: Teams owned by this user
        team_memberships: Teams this user is a member of
        created_tasks: Tasks created by this user
    """
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owned_teams = relationship(
        "Team", back_populates="owner", cascade="all, delete-orphan")
    team_memberships = relationship(
        "Team", secondary="team_members", back_populates="members")
    created_tasks = relationship("Task", back_populates="created_by_user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"

    def has_permission(self, required_role: UserRole) -> bool:
        """
        Check if user has the required permission level.

        Args:
            required_role: The minimum role required

        Returns:
            bool: True if user has sufficient permissions
        """
        role_hierarchy = {
            UserRole.AGENT: 0,
            UserRole.MEMBER: 1,
            UserRole.DIRECTOR: 2,
            UserRole.ADMIN: 3
        }

        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    def is_director(self) -> bool:
        """Check if user is a director or admin."""
        return self.role in [UserRole.DIRECTOR, UserRole.ADMIN]
