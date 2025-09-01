"""Add missing fields to all models

Revision ID: 9fd2bf43a694
Revises: af748ecd03e8
Create Date: 2025-09-01 12:33:39.998261

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9fd2bf43a694"
down_revision: Union[str, Sequence[str], None] = "af748ecd03e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing fields to users table
    op.add_column('users', sa.Column('is_active', sa.Boolean(),
                  nullable=False, server_default='true'))
    op.add_column('users', sa.Column(
        'last_login', sa.DateTime(timezone=True), nullable=True))

    # Add missing fields to teams table
    op.add_column('teams', sa.Column('is_active', sa.Boolean(),
                  nullable=False, server_default='true'))

    # Add missing fields to agents table
    op.add_column('agents', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('agents', sa.Column(
        'owner_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('agents', sa.Column('performance_metrics',
                  postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('agents', sa.Column(
        'last_active', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agents', sa.Column('is_approved', sa.Boolean(),
                  nullable=False, server_default='false'))
    op.add_column('agents', sa.Column(
        'version', sa.String(length=20), nullable=True))

    # Make team_id nullable for agents (agents can exist without teams initially)
    op.alter_column('agents', 'team_id', nullable=True)

    # Add foreign key constraint for agent owner
    op.create_foreign_key('fk_agents_owner_id', 'agents',
                          'users', ['owner_id'], ['id'])

    # Add missing fields to tasks table
    op.add_column('tasks', sa.Column('parent_task_id',
                  postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column(
        'task_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('tasks', sa.Column(
        'due_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column(
        'estimated_duration', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column(
        'actual_duration', sa.Integer(), nullable=True))

    # Make team_id nullable for tasks (tasks can exist without teams)
    op.alter_column('tasks', 'team_id', nullable=True)

    # Add foreign key constraint for parent task
    op.create_foreign_key('fk_tasks_parent_task_id', 'tasks',
                          'tasks', ['parent_task_id'], ['id'])

    # Create task dependencies association table
    op.create_table(
        'task_dependencies',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_id', postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['dependency_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('task_id', 'dependency_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop task dependencies table
    op.drop_table('task_dependencies')

    # Remove foreign key constraints
    op.drop_constraint('fk_tasks_parent_task_id', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_agents_owner_id', 'agents', type_='foreignkey')

    # Remove added columns from tasks table
    op.drop_column('tasks', 'actual_duration')
    op.drop_column('tasks', 'estimated_duration')
    op.drop_column('tasks', 'due_date')
    op.drop_column('tasks', 'task_metadata')
    op.drop_column('tasks', 'parent_task_id')

    # Restore team_id as not nullable for tasks
    op.alter_column('tasks', 'team_id', nullable=False)

    # Remove added columns from agents table
    op.drop_column('agents', 'version')
    op.drop_column('agents', 'is_approved')
    op.drop_column('agents', 'last_active')
    op.drop_column('agents', 'performance_metrics')
    op.drop_column('agents', 'owner_id')
    op.drop_column('agents', 'description')

    # Restore team_id as not nullable for agents
    op.alter_column('agents', 'team_id', nullable=False)

    # Remove added columns from teams table
    op.drop_column('teams', 'is_active')

    # Remove added columns from users table
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_active')
