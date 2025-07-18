"""remove api key system

Revision ID: 1a4a698287ce
Revises: b147dd0b1522
Create Date: 2025-07-18 13:36:37.128370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1a4a698287ce'
down_revision: Union[str, None] = 'b147dd0b1522'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove API key system completely."""
    print("Removing API key system...")

    # Drop foreign key constraint first, then drop the junction table
    print("Dropping api_key_permissions table...")
    op.drop_table('api_key_permissions')

    # Drop the main api_keys table
    print("Dropping api_keys table...")
    op.drop_index('ix_api_keys_key', table_name='api_keys')
    op.drop_table('api_keys')

    print("API key system removal completed.")


def downgrade() -> None:
    """Recreate API key system."""
    print("Recreating API key system...")

    # Recreate api_keys table
    print("Creating api_keys table...")
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on key column
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)

    # Recreate api_key_permissions table
    print("Creating api_key_permissions table...")
    op.create_table(
        'api_key_permissions',
        sa.Column('api_key_id', postgresql.UUID(), nullable=False),
        sa.Column('permission_id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.PrimaryKeyConstraint('api_key_id', 'permission_id')
    )

    print("API key system recreation completed.")
