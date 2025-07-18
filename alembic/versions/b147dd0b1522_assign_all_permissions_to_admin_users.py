"""assign all permissions to admin users

Revision ID: b147dd0b1522
Revises: 1230ffc57f64
Create Date: 2025-07-18 13:32:21.836679

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b147dd0b1522'
down_revision: Union[str, None] = '1230ffc57f64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Assign all permissions to admin users."""
    # Create a connection to execute raw SQL
    connection = op.get_bind()

    # Get all admin users
    admin_users_query = """
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.role_id = ur.id
        WHERE ur.name = 'Admin'
    """
    admin_users = connection.execute(sa.text(admin_users_query)).fetchall()

    if not admin_users:
        print("No admin users found. Skipping permission assignment.")
        return

    # Get all permissions
    permissions_query = "SELECT id FROM permissions"
    permissions = connection.execute(sa.text(permissions_query)).fetchall()

    if not permissions:
        print("No permissions found. Skipping permission assignment.")
        return

    # Assign all permissions to each admin user
    now = datetime.now()
    permissions_assigned = 0

    for admin_user in admin_users:
        user_id = admin_user[0]
        user_email = admin_user[1]

        # Check existing permissions for this user
        existing_permissions_query = """
            SELECT permission_id 
            FROM user_permissions 
            WHERE user_id = :user_id
        """
        existing_permissions = connection.execute(
            sa.text(existing_permissions_query),
            {'user_id': user_id}
        ).fetchall()

        existing_permission_ids = {perm[0] for perm in existing_permissions}

        # Insert missing permissions
        for permission in permissions:
            permission_id = permission[0]

            if permission_id not in existing_permission_ids:
                insert_query = """
                    INSERT INTO user_permissions (id, user_id, permission_id, created_at, updated_at)
                    VALUES (:id, :user_id, :permission_id, :created_at, :updated_at)
                """
                connection.execute(
                    sa.text(insert_query),
                    {
                        'id': uuid4(),
                        'user_id': user_id,
                        'permission_id': permission_id,
                        'created_at': now,
                        'updated_at': now
                    }
                )
                permissions_assigned += 1

    print(
        f"Assigned {permissions_assigned} permissions to {len(admin_users)} admin users.")


def downgrade() -> None:
    """Remove all permissions from admin users."""
    # Create a connection to execute raw SQL
    connection = op.get_bind()

    print("Removing all permissions from admin users...")

    # Get all admin users
    admin_users_query = """
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.role_id = ur.id
        WHERE ur.name = 'Admin'
    """
    admin_users = connection.execute(sa.text(admin_users_query)).fetchall()

    if not admin_users:
        print("No admin users found. Nothing to remove.")
        return

    # Remove all permissions from admin users
    for admin_user in admin_users:
        user_id = admin_user[0]
        user_email = admin_user[1]

        delete_query = """
            DELETE FROM user_permissions 
            WHERE user_id = :user_id
        """
        result = connection.execute(
            sa.text(delete_query),
            {'user_id': user_id}
        )

        print(
            f"Removed {result.rowcount} permissions from admin user: {user_email}")

    print("Permission removal completed.")
