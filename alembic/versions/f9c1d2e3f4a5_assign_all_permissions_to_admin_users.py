"""Assign all permissions to admin users

Revision ID: f9c1d2e3f4a5
Revises: f2b3c4d5e6f7
Create Date: 2025-08-21 12:45:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f9c1d2e3f4a5'
down_revision: Union[str, None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(connection: sa.engine.Connection, table_name: str) -> bool:
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t)"
        ),
        {"t": table_name}
    ).fetchone()
    return bool(result[0]) if result is not None else False


def upgrade() -> None:
    """Assign every permission to every user who has the 'Admin' role.

    This migration is idempotent: it skips inserting duplicate user_permissions.
    """
    connection = op.get_bind()

    # Basic table existence checks to allow this migration to run in different
    # environments where some tables may not yet be present.
    required_tables = ['users', 'user_roles', 'permissions', 'user_permissions']
    for t in required_tables:
        if not _table_exists(connection, t):
            print(f"Table '{t}' not present, skipping admin permission assignment.")
            return

    # Get all admin users
    admin_users_query = """
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.role_id = ur.id
        WHERE ur.name = 'Admin'
    """
    admin_users_result = connection.execute(sa.text(admin_users_query))
    if admin_users_result is None:
        print("Offline SQL generation or no result returned. Skipping.")
        return
    admin_users = admin_users_result.fetchall()

    if not admin_users:
        print("No admin users found. Skipping permission assignment.")
        return

    # Get all permissions
    permissions_query = "SELECT id FROM permissions"
    permissions_result = connection.execute(sa.text(permissions_query))
    if permissions_result is None:
        print("Offline SQL generation or no permissions result. Skipping.")
        return
    permissions = permissions_result.fetchall()

    if not permissions:
        print("No permissions found. Skipping permission assignment.")
        return

    # Assign permissions if missing
    now = datetime.now()
    assigned = 0

    for admin_user in admin_users:
        user_id = admin_user[0]

        existing_permissions_query = "SELECT permission_id FROM user_permissions WHERE user_id = :user_id"
        existing_result = connection.execute(sa.text(existing_permissions_query), {"user_id": user_id})
        existing = set()
        if existing_result is not None:
            existing = {row[0] for row in existing_result.fetchall()}

        for perm in permissions:
            permission_id = perm[0]
            if permission_id in existing:
                continue

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
                    'updated_at': now,
                }
            )
            assigned += 1

    print(f"Assigned {assigned} permissions to {len(admin_users)} admin users.")


def downgrade() -> None:
    """Remove all permissions from admin users.

    This reverses this migration by deleting rows from user_permissions for
    users that currently have the Admin role.
    """
    connection = op.get_bind()

    if not _table_exists(connection, 'users') or not _table_exists(connection, 'user_roles') or not _table_exists(connection, 'user_permissions'):
        print("Required tables not present for downgrade. Skipping.")
        return

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

    for admin_user in admin_users:
        user_id = admin_user[0]
        delete_query = "DELETE FROM user_permissions WHERE user_id = :user_id"
        result = connection.execute(sa.text(delete_query), {"user_id": user_id})
        try:
            rowcount = result.rowcount
        except Exception:
            rowcount = None
        print(f"Removed {rowcount if rowcount is not None else 'unknown'} permissions from admin user: {admin_user[1]}")
