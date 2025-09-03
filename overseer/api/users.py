"""
User management API endpoints for Overseer platform.

This module provides CRUD operations for user management, including
user profiles, role management, and user administration.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
from models.user import User, UserRole
from auth.dependencies import get_current_active_user, require_role
from auth.password import get_password_hash
from api.logging_config import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


# Pydantic models for request/response
class UserCreate(BaseModel):
    """User creation request model."""
    username: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.MEMBER


class UserUpdate(BaseModel):
    """User update request model."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response model."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List users with pagination and filtering.

    Requires DIRECTOR or ADMIN role to access.
    """
    # Check permissions
    if not current_user.has_permission(UserRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list users"
        )

    # Build query
    query = db.query(User)

    # Apply filters
    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()

    # Convert to response models
    user_responses = [
        UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        for user in users
    ]

    logger.info(
        f"Listed {len(users)} users (page {page}, total {total})",
        extra={
            "user_id": str(current_user.id),
            "page": page,
            "per_page": per_page,
            "total": total,
            "filters": {
                "role": role.value if role else None,
                "is_active": is_active,
                "search": search
            }
        }
    )

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
        has_prev=page > 1
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new user.

    Requires ADMIN role to access.
    """
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
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
    db.commit()
    db.refresh(db_user)

    logger.info(
        f"Created user: {user_data.username} ({user_data.email})",
        extra={
            "created_by": str(current_user.id),
            "new_user_id": str(db_user.id),
            "username": user_data.username,
            "email": user_data.email,
            "role": user_data.role.value
        }
    )

    return UserResponse(
        id=str(db_user.id),
        username=db_user.username,
        email=db_user.email,
        role=db_user.role.value,
        is_active=db_user.is_active,
        created_at=db_user.created_at.isoformat(),
        updated_at=db_user.updated_at.isoformat() if db_user.updated_at else None,
        last_login=db_user.last_login.isoformat() if db_user.last_login else None
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.

    Users can access their own profile, DIRECTOR+ can access any user.
    """
    # Get the requested user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    if user.id != current_user.id and not current_user.has_permission(UserRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this user"
        )

    logger.info(
        f"Retrieved user profile: {user.username}",
        extra={
            "requested_by": str(current_user.id),
            "user_id": str(user.id),
            "username": user.username
        }
    )

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user by ID.

    Users can update their own profile (limited fields), ADMIN can update any user.
    """
    # Get the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions and determine allowed fields
    is_self_update = user.id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)

    if not is_self_update and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this user"
        )

    # Track changes for logging
    changes = {}

    # Update allowed fields
    if user_data.username is not None:
        # Check if username is already taken
        existing_username = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        changes["username"] = {"old": user.username, "new": user_data.username}
        user.username = user_data.username

    if user_data.email is not None:
        # Check if email is already taken
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email

    # Role and active status can only be changed by admins
    if user_data.role is not None:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change user roles"
            )
        changes["role"] = {"old": user.role.value, "new": user_data.role.value}
        user.role = user_data.role

    if user_data.is_active is not None:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change user active status"
            )
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active

    # Update timestamp
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    logger.info(
        f"Updated user: {user.username}",
        extra={
            "updated_by": str(current_user.id),
            "user_id": str(user.id),
            "username": user.username,
            "changes": changes,
            "is_self_update": is_self_update
        }
    )

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID.

    Requires ADMIN role to access.
    """
    # Get the user to delete
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Store user info for logging before deletion
    deleted_username = user.username
    deleted_email = user.email

    db.delete(user)
    db.commit()

    logger.warning(
        f"Deleted user: {deleted_username} ({deleted_email})",
        extra={
            "deleted_by": str(current_user.id),
            "deleted_user_id": str(user_id),
            "username": deleted_username,
            "email": deleted_email
        }
    )

    return {"message": f"User {deleted_username} has been deleted"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Deactivate user by ID (soft delete).

    Requires ADMIN role to access.
    """
    # Get the user to deactivate
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()

    db.commit()

    logger.warning(
        f"Deactivated user: {user.username}",
        extra={
            "deactivated_by": str(current_user.id),
            "user_id": str(user.id),
            "username": user.username
        }
    )

    return {"message": f"User {user.username} has been deactivated"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Activate user by ID.

    Requires ADMIN role to access.
    """
    # Get the user to activate
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()

    db.commit()

    logger.info(
        f"Activated user: {user.username}",
        extra={
            "activated_by": str(current_user.id),
            "user_id": str(user.id),
            "username": user.username
        }
    )

    return {"message": f"User {user.username} has been activated"}
