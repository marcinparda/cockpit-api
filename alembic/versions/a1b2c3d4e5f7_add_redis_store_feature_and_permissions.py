"""add redis_store feature and permissions

Revision ID: a1b2c3d4e5f7
Revises: c6b968468f37
Create Date: 2026-03-19 12:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'c6b968468f37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FEATURE_NAME = "redis_store"
ACTIONS = ["create", "read", "update", "delete"]


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now()

    # Insert redis_store feature
    existing = connection.execute(
        sa.text("SELECT id FROM features WHERE name = :name"),
        {"name": FEATURE_NAME}
    ).fetchone()

    if existing:
        feature_id = existing[0]
    else:
        feature_id = str(uuid4())
        connection.execute(
            sa.text(
                "INSERT INTO features (id, name, created_at, updated_at) VALUES (:id, :name, :created_at, :updated_at)"
            ),
            {"id": feature_id, "name": FEATURE_NAME, "created_at": now, "updated_at": now},
        )

    # Create permissions for each action
    for action_name in ACTIONS:
        action_row = connection.execute(
            sa.text("SELECT id FROM actions WHERE name = :name"),
            {"name": action_name}
        ).fetchone()
        if action_row is None:
            continue
        action_id = action_row[0]

        perm_exists = connection.execute(
            sa.text("SELECT id FROM permissions WHERE feature_id = :fid AND action_id = :aid"),
            {"fid": feature_id, "aid": action_id}
        ).fetchone()

        if perm_exists:
            continue

        connection.execute(
            sa.text(
                "INSERT INTO permissions (id, feature_id, action_id, created_at, updated_at) VALUES (:id, :fid, :aid, :created_at, :updated_at)"
            ),
            {"id": str(uuid4()), "fid": feature_id, "aid": action_id, "created_at": now, "updated_at": now},
        )

    # Assign all redis_store permissions to Admin users
    admin_users = connection.execute(
        sa.text(
            "SELECT u.id FROM users u JOIN user_roles ur ON u.role_id = ur.id WHERE ur.name = 'Admin'"
        )
    ).fetchall()

    perm_rows = connection.execute(
        sa.text(
            "SELECT p.id FROM permissions p WHERE p.feature_id = :fid",
        ),
        {"fid": feature_id}
    ).fetchall()
    perm_ids = [r[0] for r in perm_rows]

    for user_row in admin_users:
        uid = user_row[0]
        for pid in perm_ids:
            already_assigned = connection.execute(
                sa.text(
                    "SELECT id FROM user_permissions WHERE user_id = :uid AND permission_id = :pid"
                ),
                {"uid": uid, "pid": pid}
            ).fetchone()
            if already_assigned:
                continue
            connection.execute(
                sa.text(
                    "INSERT INTO user_permissions (id, user_id, permission_id, created_at, updated_at) VALUES (:id, :uid, :pid, :created_at, :updated_at)"
                ),
                {"id": str(uuid4()), "uid": uid, "pid": pid, "created_at": now, "updated_at": now},
            )


def downgrade() -> None:
    connection = op.get_bind()

    feature_row = connection.execute(
        sa.text("SELECT id FROM features WHERE name = :name"),
        {"name": FEATURE_NAME}
    ).fetchone()

    if feature_row is None:
        return

    feature_id = feature_row[0]

    perm_rows = connection.execute(
        sa.text("SELECT id FROM permissions WHERE feature_id = :fid"),
        {"fid": feature_id}
    ).fetchall()
    perm_ids = [r[0] for r in perm_rows]

    for pid in perm_ids:
        connection.execute(
            sa.text("DELETE FROM user_permissions WHERE permission_id = :pid"),
            {"pid": pid}
        )

    connection.execute(
        sa.text("DELETE FROM permissions WHERE feature_id = :fid"),
        {"fid": feature_id}
    )

    connection.execute(
        sa.text("DELETE FROM features WHERE id = :fid"),
        {"fid": feature_id}
    )
