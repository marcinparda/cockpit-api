"""add_utils_feature

Revision ID: f8f54e6ca6b7
Revises: e5be391de3fe
Create Date: 2025-07-17 09:36:10.406839

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from src.app.auth.enums.actions import Actions


# revision identifiers, used by Alembic.
revision: str = 'f8f54e6ca6b7'
down_revision: Union[str, None] = 'e5be391de3fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add utils feature and its permissions."""
    connection = op.get_bind()
    now = datetime.now()

    # 1. Insert the utils feature
    utils_feature_id = str(uuid.uuid4())
    connection.execute(
        text("""
        INSERT INTO features (id, name, created_at, updated_at)
        VALUES (:id, :name, :created_at, :updated_at)
        """),
        {
            "id": utils_feature_id,
            "name": "utils",
            "created_at": now,
            "updated_at": now
        }
    )

    # 2. Get all action IDs
    actions = [Actions.CREATE, Actions.READ, Actions.UPDATE, Actions.DELETE]
    action_ids = {}

    for action in actions:
        result = connection.execute(
            text("SELECT id FROM actions WHERE name = :name"),
            {"name": action.value}
        )
        # When running in Alembic offline/static SQL generation, execute() may return None.
        if result is None:
            continue
        action_row = result.fetchone()
        if action_row:
            action_ids[action.value] = action_row[0]

    # 3. Create permissions for utils feature
    permission_ids = []
    for action in actions:
        if action.value in action_ids:
            permission_id = str(uuid.uuid4())
            permission_ids.append(permission_id)
            connection.execute(
                text("""
                INSERT INTO permissions (id, feature_id, action_id, created_at, updated_at)
                VALUES (:id, :feature_id, :action_id, :created_at, :updated_at)
                """),
                {
                    "id": permission_id,
                    "feature_id": utils_feature_id,
                    "action_id": action_ids[action.value],
                    "created_at": now,
                    "updated_at": now
                }
            )

    # 4. Grant all utils permissions to existing admin API keys
    admin_keys_result = connection.execute(
        text("SELECT id FROM api_keys WHERE is_active = true")
    )
    if admin_keys_result is None:
        admin_keys = []
    else:
        admin_keys = admin_keys_result

    for api_key_row in admin_keys:
        api_key_id = api_key_row[0]
        for permission_id in permission_ids:
            # Check if permission already exists to avoid duplicates
            existing_result = connection.execute(
                text("""
                SELECT 1 FROM api_key_permissions 
                WHERE api_key_id = :api_key_id AND permission_id = :permission_id
                """),
                {"api_key_id": api_key_id, "permission_id": permission_id}
            )

            exists = False
            if existing_result is not None:
                existing = existing_result.fetchone()
                exists = bool(existing)

            if not exists:
                connection.execute(
                    text("""
                    INSERT INTO api_key_permissions (api_key_id, permission_id, created_at, updated_at)
                    VALUES (:api_key_id, :permission_id, :created_at, :updated_at)
                    """),
                    {
                        "api_key_id": api_key_id,
                        "permission_id": permission_id,
                        "created_at": now,
                        "updated_at": now
                    }
                )


def downgrade() -> None:
    """Remove utils feature and its permissions."""
    connection = op.get_bind()

    # 1. Get utils feature ID
    result = connection.execute(
        text("SELECT id FROM features WHERE name = 'utils'")
    )
    feature_row = None
    if result is not None:
        feature_row = result.fetchone()

    if feature_row:
        utils_feature_id = feature_row[0]

        # 2. Remove API key permissions for utils
        connection.execute(
            text("""
            DELETE FROM api_key_permissions 
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE feature_id = :feature_id
            )
            """),
            {"feature_id": utils_feature_id}
        )

        # 3. Remove permissions for utils feature
        connection.execute(
            text("DELETE FROM permissions WHERE feature_id = :feature_id"),
            {"feature_id": utils_feature_id}
        )

        # 4. Remove utils feature
        connection.execute(
            text("DELETE FROM features WHERE id = :id"),
            {"id": utils_feature_id}
        )
