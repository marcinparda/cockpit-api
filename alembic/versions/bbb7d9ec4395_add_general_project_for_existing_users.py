"""add_general_project_for_existing_users

Revision ID: bbb7d9ec4395
Revises: c3d4e5f6a7b8
Create Date: 2025-08-23 10:42:14.871094

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'bbb7d9ec4395'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add General project for each user that doesn't have one."""
    # Get database connection
    connection = op.get_bind()
    
    # Define table metadata for inserts
    todo_projects_table = sa.table('todo_projects',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('owner_id', UUID(as_uuid=True)),
        sa.column('is_general', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    # Find users who don't have a General project
    users_without_general = connection.execute(
        sa.text("""
            SELECT u.id, u.email
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM todo_projects tp 
                WHERE tp.owner_id = u.id 
                AND tp.is_general = true
            )
        """)
    ).fetchall()
    
    # Create General project for each user without one
    now = datetime.utcnow()
    for user_row in users_without_general:
        user_id = user_row[0]  # id column
        
        connection.execute(
            todo_projects_table.insert().values(
                name="General",
                owner_id=user_id,
                is_general=True,
                created_at=now,
                updated_at=now
            )
        )


def downgrade() -> None:
    """Remove General projects added by this migration."""
    # Get database connection
    connection = op.get_bind()
    
    # Remove all General projects (this migration only added General projects)
    connection.execute(
        sa.text("""
            DELETE FROM todo_projects 
            WHERE name = 'General' AND is_general = true
        """)
    )
