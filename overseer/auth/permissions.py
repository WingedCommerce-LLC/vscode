"""
Role-based access control and permissions for Overseer platform.

This module provides decorators and functions for enforcing role-based access control.
"""

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status, Depends
from models.user import User, UserRole
from .dependencies import get_current_active_user


def require_role(required_role: UserRole):
    """
    Decorator to require a specific user role for endpoint access.

    Args:
        required_role: The minimum role required to access the endpoint

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or not has_role(current_user, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to require admin role for endpoint access.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_director(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to require director role or higher for endpoint access.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The director user

    Raises:
        HTTPException: If user is not a director or admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Director access required"
        )
    return current_user


def require_member(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to require member role or higher for endpoint access.

    Args:
        current_user: The current authenticated user

    Returns:
        User: The member user

    Raises:
        HTTPException: If user is not a member, director, or admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.DIRECTOR, UserRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member access required"
        )
    return current_user


def has_role(user: User, required_role: UserRole) -> bool:
    """
    Check if a user has the required role or higher.

    Args:
        user: The user to check
        required_role: The minimum required role

    Returns:
        bool: True if user has required role or higher
    """
    role_hierarchy = {
        UserRole.AGENT: 0,
        UserRole.MEMBER: 1,
        UserRole.DIRECTOR: 2,
        UserRole.ADMIN: 3
    }

    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level


def can_manage_team(user: User, team_owner_id: str) -> bool:
    """
    Check if a user can manage a specific team.

    Args:
        user: The user to check
        team_owner_id: The ID of the team owner

    Returns:
        bool: True if user can manage the team
    """
    # Admins can manage any team
    if user.role == UserRole.ADMIN:
        return True

    # Team owners can manage their own teams
    if str(user.id) == team_owner_id:
        return True

    return False


def can_manage_user(current_user: User, target_user: User) -> bool:
    """
    Check if a user can manage another user.

    Args:
        current_user: The user attempting to manage
        target_user: The user being managed

    Returns:
        bool: True if current_user can manage target_user
    """
    # Admins can manage anyone except other admins
    if current_user.role == UserRole.ADMIN:
        return target_user.role != UserRole.ADMIN or current_user.id == target_user.id

    # Directors can manage members and agents
    if current_user.role == UserRole.DIRECTOR:
        return target_user.role in [UserRole.MEMBER, UserRole.AGENT]

    # Users can only manage themselves
    return current_user.id == target_user.id
