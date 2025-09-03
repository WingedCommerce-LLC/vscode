"""
Authentication dependencies for FastAPI endpoints.

This module provides dependency functions for user authentication and authorization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_async_db
from models.user import User
from .jwt import verify_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Async database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)

    # Query user by username (primary identifier in token)
    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user (must be active and not disabled).

    Args:
        current_user: The current authenticated user

    Returns:
        User: The active user

    Raises:
        HTTPException: If user is inactive
    """
    if current_user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User | None:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.

    Args:
        token: JWT token from Authorization header
        db: Async database session

    Returns:
        User | None: The authenticated user or None
    """
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_role(required_roles):
    """
    Create a dependency that requires a specific role or higher.

    Args:
        required_roles: The minimum role required (single role or list of roles)

    Returns:
        A dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Handle both single role and list of roles
        if isinstance(required_roles, list):
            # Check if user has any of the required roles
            has_permission = any(current_user.has_permission(role) for role in required_roles)
            if not has_permission:
                role_names = [role.value for role in required_roles]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {', '.join(role_names)}"
                )
        else:
            # Single role check
            if not current_user.has_permission(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_roles.value}"
                )
        return current_user

    return role_checker
