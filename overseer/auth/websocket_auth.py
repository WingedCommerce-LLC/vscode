"""
WebSocket Authentication for Overseer

This module provides authentication utilities for WebSocket connections.
"""

from jose import JWTError, jwt
from typing import Optional
from fastapi import WebSocket, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from config.settings import get_settings
from api.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def get_current_user_websocket(websocket: WebSocket, db: AsyncSession) -> Optional[User]:
    """
    Get current user from WebSocket connection.

    This function extracts the JWT token from WebSocket query parameters
    and validates it to return the authenticated user.
    """
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return None

        # Decode JWT token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                await websocket.close(code=4001, reason="Invalid token")
                return None
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return None

        # Get user from database
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None:
            await websocket.close(code=4001, reason="User not found")
            return None

        if not user.is_active.is_(True):
            await websocket.close(code=4001, reason="User account disabled")
            return None

        return user

    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=4000, reason="Authentication failed")
        return None


async def authenticate_websocket_token(token: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate a WebSocket token and return the user.

    This is a helper function for token validation without WebSocket closure.
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            return None

        # Get user from database
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active.is_(True):
            return None

        return user

    except JWTError:
        return None
    except Exception as e:
        logger.error(f"Token authentication error: {str(e)}")
        return None
