"""Add admin API key with permissions

Revision ID: 7d2e4c9a8f1b
Revises: 5e8a7b23f91c
Create Date: 2025-05-07 10:00:00.000000

"""
from typing import Sequence, Union
import uuid
import secrets
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = '7d2e4c9a8f1b'
down_revision: Union[str, None] = '5e8a7b23f91c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add admin API key with all permissions."""
    # Create a database connection
    connection = op.get_bind()

    # Generate a secure random API key
    api_key_string = secrets.token_urlsafe(32)

    # Generate a UUID for the API key record
    api_key_id = str(uuid.uuid4())
    now = datetime.now()

    # Insert the admin API key
    connection.execute(
        text("""
        INSERT INTO api_keys (id, key, is_active, created_at, updated_at)
        VALUES (:id, :key, :is_active, :created_at, :updated_at)
        """),
        {
            "id": api_key_id,
            "key": api_key_string,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
    )

    # Get all permission IDs from the permissions table
    result = connection.execute(text("SELECT id FROM permissions"))
    permission_ids = [row[0] for row in result]

    # Create associations between the API key and all permissions
    for permission_id in permission_ids:
        connection.execute(
            text("""
            INSERT INTO api_key_permissions 
            (api_key_id, permission_id, created_at, updated_at)
            VALUES (:api_key_id, :permission_id, :created_at, :updated_at)
            """),
            {
                "api_key_id": api_key_id,
                "permission_id": permission_id,
                "created_at": now,
                "updated_at": now
            }
        )

    # Print the API key for initial setup (will show in migration logs)
    print("\n\n============================================")
    print(f"Created Admin API Key: {api_key_string}")
    print("Please store this key safely, it won't be shown again.")
    print("============================================\n\n")


def downgrade() -> None:
    """Remove the admin API key and its permission associations."""
    connection = op.get_bind()

    # Find the admin API key (assuming it's the one with all permissions)
    result = connection.execute(
        text("""
        SELECT api_key_id, COUNT(*) as permission_count 
        FROM api_key_permissions
        GROUP BY api_key_id
        ORDER BY permission_count DESC, api_key_id
        LIMIT 1
        """)
    )
    row = result.fetchone()

    if row is not None:
        admin_key_id = row[0]

        # Delete the API key's permission associations
        connection.execute(
            text("DELETE FROM api_key_permissions WHERE api_key_id = :id"),
            {"id": admin_key_id}
        )

        # Delete the API key itself
        connection.execute(
            text("DELETE FROM api_keys WHERE id = :id"),
            {"id": admin_key_id}
        )
