"""Update API keys table structure

Revision ID: f28374a12c5d
Revises: 9593044e866a
Create Date: 2025-05-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f28374a12c5d'
down_revision: Union[str, None] = '9593044e866a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid-ossp extension to use uuid_generate_v4()
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Drop primary key from 'key' column
    op.drop_constraint('api_keys_pkey', 'api_keys', type_='primary')

    # Change id column type to UUID
    op.alter_column('api_keys', 'id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using="uuid_generate_v4()",  # Convert existing IDs to UUIDs
                    existing_nullable=False,
                    autoincrement=False)

    # Add primary key constraint to id column
    op.create_primary_key('api_keys_pkey', 'api_keys', ['id'])

    # Add index to key column if it doesn't exist
    op.create_index(op.f('ix_api_keys_key'), 'api_keys', ['key'], unique=True)

    # Add is_active column
    op.add_column('api_keys',
                  sa.Column('is_active', sa.Boolean(),
                            server_default=sa.text('true'), nullable=False))

    # Add created_by column
    op.add_column('api_keys',
                  sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    # Remove created_by column
    op.drop_column('api_keys', 'created_by')

    # Remove is_active column
    op.drop_column('api_keys', 'is_active')

    # Drop index on key column
    op.drop_index(op.f('ix_api_keys_key'), table_name='api_keys')

    # Drop primary key from id column
    op.drop_constraint('api_keys_pkey', 'api_keys', type_='primary')

    # Change id column back to Integer
    op.alter_column('api_keys', 'id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    autoincrement=True,
                    existing_nullable=False)

    # Set key column as primary key again
    op.create_primary_key('api_keys_pkey', 'api_keys', ['key'])
