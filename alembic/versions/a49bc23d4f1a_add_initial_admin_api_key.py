"""Add initial admin API key

Revision ID: a49bc23d4f1a
Revises: f28374a12c5d
Create Date: 2025-05-06 11:30:00.000000

"""
from typing import Sequence, Union
import uuid
import secrets
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a49bc23d4f1a'
down_revision: Union[str, None] = 'f28374a12c5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generate a secure random API key
    api_key = secrets.token_urlsafe(32)

    # Generate a UUID for the API key record
    api_key_id = uuid.uuid4()

    # Get admin permissions from the preset and convert to JSON string
    admin_permissions = json.dumps([])

    # Insert the admin API key
    op.execute(f"""
    INSERT INTO api_keys (id, key, permissions, is_active, created_at, updated_at)
    VALUES (
        '{api_key_id}', 
        '{api_key}', 
        '{admin_permissions}'::json, 
        TRUE, 
        NOW(), 
        NOW()
    )
    """)

    # Print the API key for initial setup (will show in migration logs)
    print(f"\n\n============================================")
    print(f"Created Admin API Key: {api_key}")
    print(f"Please store this key safely, it won't be shown again.")
    print(f"============================================\n\n")


def downgrade() -> None:
    # Remove the admin API key (using a safe approach, only delete keys with admin permissions)
    op.execute("""
    DELETE FROM api_keys 
    WHERE permissions::text @> '{"api_keys":["create","read","update","delete"]}'::jsonb 
    AND permissions::text @> '{"categories":["create","read","update","delete"]}'::jsonb
    AND permissions::text @> '{"expenses":["create","read","update","delete"]}'::jsonb
    AND permissions::text @> '{"payment_methods":["create","read","update","delete"]}'::jsonb
    AND created_at = (SELECT MIN(created_at) FROM api_keys)
    LIMIT 1
    """)
