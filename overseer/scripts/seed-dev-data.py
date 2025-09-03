#!/usr/bin/env python3
"""
Development Data Seeding Script

This script creates sample data for development and testing purposes.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from models.user import User, UserRole
from models.team import Team
from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus, TaskPriority
from auth.password import get_password_hash


async def create_sample_users(db: AsyncSession):
    """Create sample users for development."""
    print("Creating sample users...")

    users = [
        {
            "username": "admin",
            "email": "admin@overseer.dev",
            "password": "admin123",
            "role": UserRole.ADMIN
        },
        {
            "username": "director1",
            "email": "director1@overseer.dev",
            "password": "director123",
            "role": UserRole.DIRECTOR
        },
        {
            "username": "director2",
            "email": "director2@overseer.dev",
            "password": "director123",
            "role": UserRole.DIRECTOR
        },
        {
            "username": "member1",
            "email": "member1@overseer.dev",
            "password": "member123",
            "role": UserRole.MEMBER
        },
        {
            "username": "member2",
            "email": "member2@overseer.dev",
            "password": "member123",
            "role": UserRole.MEMBER
        }
    ]

    created_users = []
    for user_data in users:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=get_password_hash(user_data["password"]),
            role=user_data["role"]
        )
        db.add(user)
        created_users.append(user)

    await db.commit()
    print(f"✅ Created {len(created_users)} users")
    return created_users


async def create_sample_teams(db: AsyncSession, users: list):
    """Create sample teams for development."""
    print("Creating sample teams...")

    # Find directors to own teams
    directors = [u for u in users if u.role == UserRole.DIRECTOR]
    members = [u for u in users if u.role == UserRole.MEMBER]

    teams_data = [
        {
            "name": "AI Development Team",
            "description": "Team focused on AI agent development and deployment",
            "owner": directors[0],
            "members": [members[0]]
        },
        {
            "name": "Platform Engineering",
            "description": "Team responsible for platform infrastructure and tooling",
            "owner": directors[1] if len(directors) > 1 else directors[0],
            "members": [members[1]] if len(members) > 1 else []
        }
    ]

    created_teams = []
    for team_data in teams_data:
        team = Team(
            name=team_data["name"],
            description=team_data["description"],
            owner_id=team_data["owner"].id
        )
        db.add(team)
        await db.flush()  # Get the team ID

        # Add members
        for member in team_data["members"]:
            team.members.append(member)

        created_teams.append(team)

    await db.commit()
    print(f"✅ Created {len(created_teams)} teams")
    return created_teams


async def create_sample_agents(db: AsyncSession, teams: list, users: list):
    """Create sample agents for development."""
    print("Creating sample agents...")

    directors = [u for u in users if u.role == UserRole.DIRECTOR]

    agents_data = [
        {
            "name": "CodeGen Agent",
            "description": "AI agent specialized in code generation and refactoring",
            "type": AgentType.CODER,
            "team": teams[0],
            "owner": directors[0],
            "capabilities": ["python", "javascript", "code-review", "testing"],
            "status": AgentStatus.ACTIVE
        },
        {
            "name": "QA Agent",
            "description": "AI agent for automated testing and quality assurance",
            "type": AgentType.TESTER,
            "team": teams[0],
            "owner": directors[0],
            "capabilities": ["automated-testing", "bug-detection", "performance-testing"],
            "status": AgentStatus.ACTIVE
        },
        {
            "name": "DevOps Agent",
            "description": "AI agent for deployment and infrastructure management",
            "type": AgentType.GENERAL,
            "team": teams[1] if len(teams) > 1 else teams[0],
            "owner": directors[1] if len(directors) > 1 else directors[0],
            "capabilities": ["docker", "kubernetes", "ci-cd", "monitoring"],
            "status": AgentStatus.INACTIVE
        }
    ]

    created_agents = []
    for agent_data in agents_data:
        agent = Agent(
            name=agent_data["name"],
            description=agent_data["description"],
            type=agent_data["type"],
            team_id=agent_data["team"].id,
            owner_id=agent_data["owner"].id,
            capabilities=agent_data["capabilities"],
            status=agent_data["status"],
            is_approved=True
        )
        db.add(agent)
        created_agents.append(agent)

    await db.commit()
    print(f"✅ Created {len(created_agents)} agents")
    return created_agents


async def create_sample_tasks(db: AsyncSession, teams: list, agents: list, users: list):
    """Create sample tasks for development."""
    print("Creating sample tasks...")

    directors = [u for u in users if u.role == UserRole.DIRECTOR]

    tasks_data = [
        {
            "title": "Implement user authentication API",
            "description": "Create JWT-based authentication system with role-based access control",
            "team": teams[0],
            "assigned_agent": agents[0],
            "created_by": directors[0],
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH
        },
        {
            "title": "Set up automated testing pipeline",
            "description": "Configure CI/CD pipeline with automated testing and coverage reporting",
            "team": teams[0],
            "assigned_agent": agents[1],
            "created_by": directors[0],
            "status": TaskStatus.PENDING,
            "priority": TaskPriority.NORMAL
        },
        {
            "title": "Deploy development environment",
            "description": "Set up Docker-based development environment with hot reload",
            "team": teams[1] if len(teams) > 1 else teams[0],
            "assigned_agent": agents[2],
            "created_by": directors[1] if len(directors) > 1 else directors[0],
            "status": TaskStatus.COMPLETED,
            "priority": TaskPriority.HIGH
        }
    ]

    created_tasks = []
    for task_data in tasks_data:
        task = Task(
            title=task_data["title"],
            description=task_data["description"],
            team_id=task_data["team"].id,
            assigned_agent_id=task_data["assigned_agent"].id,
            created_by_id=task_data["created_by"].id,
            status=task_data["status"],
            priority=task_data["priority"]
        )
        db.add(task)
        created_tasks.append(task)

    await db.commit()
    print(f"✅ Created {len(created_tasks)} tasks")
    return created_tasks


async def main():
    """Main seeding function."""
    print("🌱 Seeding development data...")
    print()

    try:
        # Get database session
        async for db in get_async_db():
            # Create sample data
            users = await create_sample_users(db)
            teams = await create_sample_teams(db, users)
            agents = await create_sample_agents(db, teams, users)
            tasks = await create_sample_tasks(db, teams, agents, users)

            print()
            print("🎉 Development data seeding completed!")
            print()
            print("📋 Created:")
            print(f"   • {len(users)} users")
            print(f"   • {len(teams)} teams")
            print(f"   • {len(agents)} agents")
            print(f"   • {len(tasks)} tasks")
            print()
            print("🔑 Login credentials:")
            print("   • Admin: admin / admin123")
            print("   • Director: director1 / director123")
            print("   • Member: member1 / member123")
            print()
            break

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
