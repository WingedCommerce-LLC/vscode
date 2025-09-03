"""
Team management API endpoints for Overseer platform.

This module provides CRUD operations for team management, including
team creation, member management, and team administration.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.user import User, UserRole
from models.team import Team
from auth.dependencies import get_current_active_user, require_role
from api.logging_config import get_logger

router = APIRouter(prefix="/teams", tags=["teams"])
logger = get_logger(__name__)


# Pydantic models for request/response
class TeamCreate(BaseModel):
    """Team creation request model."""
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    """Team update request model."""
    name: Optional[str] = None
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    """Team member response model."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    joined_at: str

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Team response model."""
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: str
    updated_at: Optional[str] = None
    member_count: int
    members: Optional[List[TeamMemberResponse]] = None

    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    """Team list response model."""
    teams: List[TeamResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class AddMemberRequest(BaseModel):
    """Add member to team request model."""
    user_id: UUID


@router.get("/", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by team name"),
    include_members: bool = Query(False, description="Include team members in response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List teams with pagination and filtering.

    Users see teams they own or are members of.
    DIRECTOR+ can see all teams.
    """
    # Build query based on user permissions
    if current_user.has_permission(UserRole.DIRECTOR):
        # Directors and admins can see all teams
        query = db.query(Team)
    else:
        # Regular users can only see teams they own or are members of
        query = db.query(Team).filter(
            (Team.owner_id == current_user.id) |
            (Team.members.any(User.id == current_user.id))
        )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(Team.name.ilike(search_term))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    teams = query.offset(offset).limit(per_page).all()

    # Convert to response models
    team_responses = []
    for team in teams:
        team_response = TeamResponse(
            id=str(team.id),
            name=team.name,
            description=team.description,
            owner_id=str(team.owner_id),
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat() if team.updated_at else None,
            member_count=len(team.members)
        )

        # Include members if requested
        if include_members:
            team_response.members = [
                TeamMemberResponse(
                    id=str(member.id),
                    username=member.username,
                    email=member.email,
                    role=member.role.value,
                    is_active=member.is_active,
                    joined_at=member.created_at.isoformat()  # Using user creation as join date for now
                )
                for member in team.members
            ]

        team_responses.append(team_response)

    logger.info(
        f"Listed {len(teams)} teams (page {page}, total {total})",
        extra={
            "user_id": str(current_user.id),
            "page": page,
            "per_page": per_page,
            "total": total,
            "search": search,
            "include_members": include_members
        }
    )

    return TeamListResponse(
        teams=team_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
        has_prev=page > 1
    )


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new team.

    Any authenticated user can create a team and becomes the owner.
    """
    # Check if team name already exists
    existing_team = db.query(Team).filter(Team.name == team_data.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists"
        )

    # Create new team
    db_team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=current_user.id
    )

    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    # Add owner as a member
    db_team.members.append(current_user)
    db.commit()

    logger.info(
        f"Created team: {team_data.name}",
        extra={
            "created_by": str(current_user.id),
            "team_id": str(db_team.id),
            "team_name": team_data.name
        }
    )

    return TeamResponse(
        id=str(db_team.id),
        name=db_team.name,
        description=db_team.description,
        owner_id=str(db_team.owner_id),
        created_at=db_team.created_at.isoformat(),
        updated_at=db_team.updated_at.isoformat() if db_team.updated_at else None,
        member_count=1  # Owner is automatically a member
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    include_members: bool = Query(False, description="Include team members in response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get team by ID.

    Users can access teams they own or are members of.
    DIRECTOR+ can access any team.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_member = current_user in team.members
    is_director = current_user.has_permission(UserRole.DIRECTOR)

    if not (is_owner or is_member or is_director):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this team"
        )

    team_response = TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat() if team.updated_at else None,
        member_count=len(team.members)
    )

    # Include members if requested
    if include_members:
        team_response.members = [
            TeamMemberResponse(
                id=str(member.id),
                username=member.username,
                email=member.email,
                role=member.role.value,
                is_active=member.is_active,
                joined_at=member.created_at.isoformat()
            )
            for member in team.members
        ]

    logger.info(
        f"Retrieved team: {team.name}",
        extra={
            "requested_by": str(current_user.id),
            "team_id": str(team.id),
            "team_name": team.name,
            "include_members": include_members
        }
    )

    return team_response


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update team by ID.

    Only team owners and admins can update teams.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can update teams"
        )

    # Track changes for logging
    changes = {}

    # Update fields
    if team_data.name is not None:
        # Check if new name already exists
        existing_team = db.query(Team).filter(
            Team.name == team_data.name,
            Team.id != team_id
        ).first()
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team name already exists"
            )
        changes["name"] = {"old": team.name, "new": team_data.name}
        team.name = team_data.name

    if team_data.description is not None:
        changes["description"] = {"old": team.description, "new": team_data.description}
        team.description = team_data.description

    # Update timestamp
    team.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(team)

    logger.info(
        f"Updated team: {team.name}",
        extra={
            "updated_by": str(current_user.id),
            "team_id": str(team.id),
            "team_name": team.name,
            "changes": changes
        }
    )

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat() if team.updated_at else None,
        member_count=len(team.members)
    )


@router.delete("/{team_id}")
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete team by ID.

    Only team owners and admins can delete teams.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can delete teams"
        )

    # Store team info for logging before deletion
    deleted_team_name = team.name
    member_count = len(team.members)

    db.delete(team)
    db.commit()

    logger.warning(
        f"Deleted team: {deleted_team_name}",
        extra={
            "deleted_by": str(current_user.id),
            "team_id": str(team_id),
            "team_name": deleted_team_name,
            "member_count": member_count
        }
    )

    return {"message": f"Team {deleted_team_name} has been deleted"}


@router.post("/{team_id}/members", response_model=TeamResponse)
async def add_team_member(
    team_id: UUID,
    member_data: AddMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to a team.

    Only team owners and admins can add members.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can add members"
        )

    # Get the user to add
    user_to_add = db.query(User).filter(User.id == member_data.user_id).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is already a member
    if user_to_add in team.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )

    # Add user to team
    team.members.append(user_to_add)
    team.updated_at = datetime.utcnow()
    db.commit()

    logger.info(
        f"Added member {user_to_add.username} to team {team.name}",
        extra={
            "added_by": str(current_user.id),
            "team_id": str(team.id),
            "team_name": team.name,
            "new_member_id": str(user_to_add.id),
            "new_member_username": user_to_add.username
        }
    )

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat() if team.updated_at else None,
        member_count=len(team.members)
    )


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from a team.

    Team owners and admins can remove any member.
    Users can remove themselves from teams.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Get the user to remove
    user_to_remove = db.query(User).filter(User.id == user_id).first()
    if not user_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is a member
    if user_to_remove not in team.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this team"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)
    is_self_removal = user_id == current_user.id

    if not (is_owner or is_admin or is_self_removal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to remove this member"
        )

    # Prevent owner from removing themselves
    if user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team owner cannot be removed from the team"
        )

    # Remove user from team
    team.members.remove(user_to_remove)
    team.updated_at = datetime.utcnow()
    db.commit()

    logger.info(
        f"Removed member {user_to_remove.username} from team {team.name}",
        extra={
            "removed_by": str(current_user.id),
            "team_id": str(team.id),
            "team_name": team.name,
            "removed_member_id": str(user_to_remove.id),
            "removed_member_username": user_to_remove.username,
            "is_self_removal": is_self_removal
        }
    )

    return {"message": f"User {user_to_remove.username} has been removed from team {team.name}"}


@router.post("/{team_id}/transfer-ownership")
async def transfer_team_ownership(
    team_id: UUID,
    new_owner_data: AddMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Transfer team ownership to another member.

    Only current team owners and admins can transfer ownership.
    """
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check permissions
    is_owner = team.owner_id == current_user.id
    is_admin = current_user.has_permission(UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can transfer ownership"
        )

    # Get the new owner
    new_owner = db.query(User).filter(User.id == new_owner_data.user_id).first()
    if not new_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New owner not found"
        )

    # Check if new owner is a team member
    if new_owner not in team.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New owner must be a team member"
        )

    # Prevent transferring to current owner
    if new_owner.id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already the team owner"
        )

    # Transfer ownership
    old_owner_id = team.owner_id
    team.owner_id = new_owner.id
    team.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        f"Transferred ownership of team {team.name} to {new_owner.username}",
        extra={
            "transferred_by": str(current_user.id),
            "team_id": str(team.id),
            "team_name": team.name,
            "old_owner_id": str(old_owner_id),
            "new_owner_id": str(new_owner.id),
            "new_owner_username": new_owner.username
        }
    )

    return {"message": f"Team ownership transferred to {new_owner.username}"}
