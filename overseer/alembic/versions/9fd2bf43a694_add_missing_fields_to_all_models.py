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
    # Add missing fields to agents table (only fields not already in first migration)
    op.add_column('agents', sa.Column('performance_metrics',
                  postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('agents', sa.Column('is_approved', sa.Boolean(),
                  nullable=False, server_default='false'))
    op.add_column('agents', sa.Column(
        'version', sa.String(length=20), nullable=True))

    # Add missing fields to tasks table (only fields not already in first migration)
    op.add_column('tasks', sa.Column(
        'task_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('tasks', sa.Column(
        'estimated_duration', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column(
        'actual_duration', sa.Integer(), nullable=True))

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

    # Remove added columns from tasks table
    op.drop_column('tasks', 'actual_duration')
    op.drop_column('tasks', 'estimated_duration')
    op.drop_column('tasks', 'task_metadata')

    # Remove added columns from agents table
    op.drop_column('agents', 'version')
    op.drop_column('agents', 'is_approved')
    op.drop_column('agents', 'performance_metrics')
