"""remove_shared_feature_and_permissions

Revision ID: 8650ef3eeec7
Revises: bbb7d9ec4395
Create Date: 2025-08-23 12:28:01.279145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8650ef3eeec7'
down_revision: Union[str, None] = 'bbb7d9ec4395'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove shared feature and related permissions."""
    # First, delete user permissions that reference shared feature permissions
    op.execute("""
    DELETE FROM user_permissions 
    WHERE permission_id IN (
        SELECT p.id FROM permissions p 
        JOIN features f ON p.feature_id = f.id 
        WHERE f.name = 'shared'
    )
    """)
    
    # Delete permissions that reference the shared feature
    op.execute("""
    DELETE FROM permissions 
    WHERE feature_id IN (
        SELECT id FROM features WHERE name = 'shared'
    )
    """)
    
    # Finally, delete the shared feature itself
    op.execute("DELETE FROM features WHERE name = 'shared'")


def downgrade() -> None:
    """Re-create shared feature (but not permissions - they would be empty)."""
    # Re-create the shared feature
    op.execute("""
    INSERT INTO features (id, name, created_at, updated_at) 
    VALUES (uuid_generate_v4(), 'shared', NOW(), NOW())
    ON CONFLICT (name) DO NOTHING
    """)
