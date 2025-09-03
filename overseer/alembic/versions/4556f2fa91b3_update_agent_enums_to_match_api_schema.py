"""update_agent_enums_to_match_api_schema

Revision ID: 4556f2fa91b3
Revises: 9fd2bf43a694
Create Date: 2025-09-03 14:38:19.513941

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4556f2fa91b3"
down_revision: Union[str, Sequence[str], None] = "9fd2bf43a694"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Create new enum types with API schema values
        op.execute("CREATE TYPE agentstatus_new AS ENUM ('inactive', 'active', 'busy', 'error', 'maintenance')")
        op.execute("CREATE TYPE agenttype_new AS ENUM ('coder', 'reviewer', 'tester', 'documenter', 'analyst', 'general')")

        # Update existing data to match new enum values
        # AgentStatus mapping: IDLE->inactive, BUSY->busy, OFFLINE->inactive, ERROR->error
        op.execute("""
            UPDATE agents SET status = CASE
                WHEN status = 'IDLE' THEN 'inactive'
                WHEN status = 'BUSY' THEN 'busy'
                WHEN status = 'OFFLINE' THEN 'inactive'
                WHEN status = 'ERROR' THEN 'error'
                ELSE 'inactive'
            END
        """)

        # AgentType mapping: DEVELOPER->coder, TESTER->tester, REVIEWER->reviewer, ANALYST->analyst, COORDINATOR->general
        op.execute("""
            UPDATE agents SET agent_type = CASE
                WHEN agent_type = 'DEVELOPER' THEN 'coder'
                WHEN agent_type = 'TESTER' THEN 'tester'
                WHEN agent_type = 'REVIEWER' THEN 'reviewer'
                WHEN agent_type = 'ANALYST' THEN 'analyst'
                WHEN agent_type = 'COORDINATOR' THEN 'general'
                ELSE 'general'
            END
        """)

        # Change column types to use new enums
        op.execute("ALTER TABLE agents ALTER COLUMN status TYPE agentstatus_new USING status::text::agentstatus_new")
        op.execute("ALTER TABLE agents ALTER COLUMN agent_type TYPE agenttype_new USING agent_type::text::agenttype_new")

        # Drop old enum types
        op.execute("DROP TYPE agentstatus")
        op.execute("DROP TYPE agenttype")

        # Rename new enum types to original names
        op.execute("ALTER TYPE agentstatus_new RENAME TO agentstatus")
        op.execute("ALTER TYPE agenttype_new RENAME TO agenttype")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Create old enum types
        op.execute("CREATE TYPE agentstatus_old AS ENUM ('IDLE', 'BUSY', 'OFFLINE', 'ERROR')")
        op.execute("CREATE TYPE agenttype_old AS ENUM ('DEVELOPER', 'TESTER', 'REVIEWER', 'ANALYST', 'COORDINATOR')")

        # Update data back to old enum values
        # AgentStatus mapping: inactive->IDLE, active->IDLE, busy->BUSY, error->ERROR, maintenance->OFFLINE
        op.execute("""
            UPDATE agents SET status = CASE
                WHEN status = 'inactive' THEN 'IDLE'
                WHEN status = 'active' THEN 'IDLE'
                WHEN status = 'busy' THEN 'BUSY'
                WHEN status = 'error' THEN 'ERROR'
                WHEN status = 'maintenance' THEN 'OFFLINE'
                ELSE 'IDLE'
            END
        """)

        # AgentType mapping: coder->DEVELOPER, tester->TESTER, reviewer->REVIEWER, analyst->ANALYST, general->COORDINATOR
        op.execute("""
            UPDATE agents SET agent_type = CASE
                WHEN agent_type = 'coder' THEN 'DEVELOPER'
                WHEN agent_type = 'tester' THEN 'TESTER'
                WHEN agent_type = 'reviewer' THEN 'REVIEWER'
                WHEN agent_type = 'analyst' THEN 'ANALYST'
                WHEN agent_type = 'general' THEN 'COORDINATOR'
                WHEN agent_type = 'documenter' THEN 'COORDINATOR'
                ELSE 'COORDINATOR'
            END
        """)

        # Change column types back to old enums
        op.execute("ALTER TABLE agents ALTER COLUMN status TYPE agentstatus_old USING status::text::agentstatus_old")
        op.execute("ALTER TABLE agents ALTER COLUMN agent_type TYPE agenttype_old USING agent_type::text::agenttype_old")

        # Drop new enum types
        op.execute("DROP TYPE agentstatus")
        op.execute("DROP TYPE agenttype")

        # Rename old enum types back to original names
        op.execute("ALTER TYPE agentstatus_old RENAME TO agentstatus")
        op.execute("ALTER TYPE agenttype_old RENAME TO agenttype")
