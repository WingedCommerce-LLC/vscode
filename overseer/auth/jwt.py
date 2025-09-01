"""
JWT token management utilities for Overseer platform.

This module provides JWT token creation, validation, and refresh functionality.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
import os


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token data model for validation."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The data to encode in the token

    Returns:
        str: The encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception) -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        credentials_exception: Exception to raise if verification fails

    Returns:
        TokenData: The decoded token data

    Raises:
        credentials_exception: If token verification fails
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id")
        role: Optional[str] = payload.get("role")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, user_id=user_id, role=role)
        return token_data

    except JWTError:
        raise credentials_exception


def verify_refresh_token(token: str, credentials_exception) -> TokenData:
    """
    Verify and decode a JWT refresh token.

    Args:
        token: The JWT refresh token to verify
        credentials_exception: Exception to raise if verification fails

    Returns:
        TokenData: The decoded token data

    Raises:
        credentials_exception: If token verification fails
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: Optional[str] = payload.get("type")

        if token_type != "refresh":
            raise credentials_exception

        username: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id")
        role: Optional[str] = payload.get("role")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, user_id=user_id, role=role)
        return token_data

    except JWTError:
        raise credentials_exception


def get_token_expiry_time() -> int:
    """
    Get the token expiry time in seconds.

    Returns:
        int: Token expiry time in seconds
    """
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
