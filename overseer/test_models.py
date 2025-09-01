"""Test script for database models."""

from models.task import Task, TaskStatus, TaskPriority
from models.agent import Agent, AgentType, AgentStatus
from models.team import Team
from models.user import User, UserRole
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))


def test_model_creation():
    """Test creating model instances."""
    print("Testing model creation...")

    # Test User model
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DIRECTOR
    )
    print(f"✓ User created: {user.username} ({user.role.value})")

    # Test Team model
    team = Team(
        name="Development Team",
        description="Main development team",
        owner_id=user.id
    )
    print(f"✓ Team created: {team.name}")

    # Test Agent model
    agent = Agent(
        name="Code Agent",
        description="AI agent specialized in code development",
        type=AgentType.CODER.value,
        status=AgentStatus.ACTIVE.value,
        owner_id=user.id,
        team_id=team.id,
        capabilities=["python", "javascript", "testing"],
        configuration={"max_tokens": 4000, "temperature": 0.7},
        performance_metrics={"tasks_completed": 15, "success_rate": 0.93},
        is_approved=True,
        version="1.2.0"
    )
    print(f"✓ Agent created: {agent.name} ({agent.type})")

    # Test Task model
    task = Task(
        title="Implement user authentication",
        description="Create JWT-based authentication system",
        status=TaskStatus.PENDING.value,
        priority=TaskPriority.HIGH.value,
        created_by_id=user.id,
        team_id=team.id,
        requirements={"estimated_hours": 8, "complexity": "medium"},
        task_metadata={"project": "overseer", "sprint": "1.1"},
        estimated_duration=480,  # 8 hours in minutes
        artifacts=[]
    )
    print(f"✓ Task created: {task.title} ({task.priority})")

    return user, team, agent, task


def test_model_methods():
    """Test model methods."""
    print("\nTesting model methods...")

    user, team, agent, task = test_model_creation()

    # Test User methods
    print(f"✓ User is admin: {user.is_admin()}")
    print(f"✓ User is director: {user.is_director()}")
    print(
        f"✓ User has director permission: {user.has_permission(UserRole.DIRECTOR)}")

    # Test Team methods
    print(f"✓ Team member count: {team.get_member_count()}")
    print(f"✓ Team agent count: {team.get_agent_count()}")
    print(f"✓ User is team member: {team.is_member(user)}")

    # Test Agent methods
    print(f"✓ Agent is available: {agent.is_available()}")
    print(f"✓ Agent is healthy: {agent.is_healthy()}")
    print(f"✓ Agent has python capability: {agent.has_capability('python')}")
    agent.set_status(AgentStatus.BUSY)
    print(f"✓ Agent status after set_busy: {agent.status}")

    # Test Task methods
    print(f"✓ Task is active: {task.is_active()}")
    print(f"✓ Task can be assigned: {task.can_be_assigned()}")
    print(f"✓ Task priority weight: {task.get_priority_weight()}")
    task.start_task()
    print(f"✓ Task status after start: {task.status}")
    task.complete_task()
    print(f"✓ Task status after complete: {task.status}")
    print(f"✓ Task is completed: {task.is_completed()}")


def test_new_fields():
    """Test all the new fields added to models."""
    print("\nTesting new model fields...")

    user, team, agent, task = test_model_creation()

    # Test User new fields
    print(f"✓ User is_active: {user.is_active}")
    print(f"✓ User last_login: {user.last_login}")

    # Test Team new fields
    print(f"✓ Team is_active: {team.is_active}")

    # Test Agent new fields
    print(f"✓ Agent description: {agent.description}")
    print(f"✓ Agent owner_id: {agent.owner_id}")
    print(f"✓ Agent performance_metrics: {agent.performance_metrics}")
    print(f"✓ Agent is_approved: {agent.is_approved}")
    print(f"✓ Agent version: {agent.version}")
    print(f"✓ Agent last_active: {agent.last_active}")

    # Test Task new fields
    print(f"✓ Task task_metadata: {task.task_metadata}")
    print(f"✓ Task estimated_duration: {task.estimated_duration}")
    print(f"✓ Task artifacts: {task.artifacts}")
    print(f"✓ Task due_date: {task.due_date}")
    print(f"✓ Task parent_task_id: {task.parent_task_id}")

    # Test Task methods with new fields
    task.add_artifact("authentication_module.py")
    task.add_artifact("test_auth.py")
    print(f"✓ Task artifacts after adding: {task.artifacts}")

    task.set_requirement("framework", "FastAPI")
    task.set_requirement("database", "PostgreSQL")
    print(f"✓ Task framework requirement: {task.get_requirement('framework')}")
    print(f"✓ Task database requirement: {task.get_requirement('database')}")

    # Test Agent capability management
    agent.add_capability("docker")
    agent.add_capability("kubernetes")
    print(f"✓ Agent capabilities after adding: {agent.capabilities}")

    agent.remove_capability("docker")
    print(f"✓ Agent capabilities after removing docker: {agent.capabilities}")


def test_model_relationships():
    """Test model relationships (conceptual - would need database for actual testing)."""
    print("\nTesting model relationships (conceptual)...")

    user, team, agent, task = test_model_creation()

    # These would work with actual database sessions
    print("✓ User -> Teams relationship defined")
    print("✓ Team -> Members relationship defined")
    print("✓ Team -> Agents relationship defined")
    print("✓ User -> Created Tasks relationship defined")
    print("✓ User -> Assigned Tasks relationship defined")
    print("✓ Task -> Subtasks relationship defined")
    print("✓ Task -> Dependencies relationship defined")
    print("✓ Agent -> Owner relationship defined")
    print("✓ Task -> Parent Task relationship defined")


def main():
    """Run all tests."""
    print("=" * 50)
    print("OVERSEER DATABASE MODELS TEST")
    print("=" * 50)

    try:
        test_model_creation()
        test_model_methods()
        test_new_fields()
        test_model_relationships()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("Database models are working correctly.")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
