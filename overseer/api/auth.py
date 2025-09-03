"""
Authentication API endpoints for Overseer platform.

This module provides user registration, login, logout, and token refresh endpoints.
"""

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_async_db
from models.user import User, UserRole
from auth.password import verify_password, get_password_hash
from auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_token_expiry_time,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token
)
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class UserRegister(BaseModel):
    """User registration request model."""
    username: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.MEMBER


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_async_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Async database session

    Returns:
        UserResponse: The created user data

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if user with email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_username = result.scalar_one_or_none()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,
        is_active=True
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=str(db_user.id),
        username=db_user.username,
        email=db_user.email,
        role=db_user.role.value,
        is_active=db_user.is_active,
        created_at=db_user.created_at.isoformat(),
        last_login=db_user.last_login.isoformat() if db_user.last_login else None
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate user and return access and refresh tokens.

    Args:
        form_data: OAuth2 password form data (username and password)
        db: Async database session

    Returns:
        LoginResponse: Access token, refresh token, and user data

    Raises:
        HTTPException: If authentication fails
    """
    # Find user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create tokens
    token_data = {
        "sub": user.username,
        "user_id": str(user.id),
        "role": user.role.value
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data=token_data)

    user_response = UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=get_token_expiry_time(),
        user=user_response
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token request data
        db: Async database session

    Returns:
        Token: New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify refresh token
    token_data = verify_refresh_token(
        refresh_data.refresh_token, credentials_exception)

    # Get user from database
    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exception

    # Create new access token
    new_token_data = {
        "sub": user.username,
        "user_id": str(user.id),
        "role": user.role.value
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=new_token_data,
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_time()
    )


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """
    Logout current user.

    Note: In a stateless JWT implementation, logout is handled client-side
    by discarding the tokens. This endpoint exists for consistency and
    future session management features.

    Args:
        current_user: The current authenticated user

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile information.

    Args:
        current_user: The current authenticated user

    Returns:
        UserResponse: Current user profile data
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.get("/verify-token")
async def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    """
    Verify if the current token is valid.

    Args:
        current_user: The current authenticated user

    Returns:
        dict: Token validity status and user info
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role.value
    }
