"""Fix actions and permissions

Revision ID: e9a1c3b2d4f5
Revises: 05eac51d9014
Create Date: 2025-08-21 12:00:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from src.app.auth.enums.actions import Actions


# revision identifiers, used by Alembic.
revision: str = 'e9a1c3b2d4f5'
down_revision: Union[str, None] = '05eac51d9014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate actions from Actions enum and rebuild permissions for all features.

    This migration removes existing user_permissions
    (they reference permissions), deletes all permissions and actions and then
    inserts actions taken from `src.auth.enums.actions.Actions`. It then
    recreates permissions for every existing feature x action pair using the
    same logic as the original seed.
    """
    connection = op.get_bind()
    now = datetime.now()

    # 1. Remove associations that reference old permissions
    connection.execute(sa.text("DELETE FROM user_permissions"))

    # 2. Remove old permissions and actions
    connection.execute(sa.text("DELETE FROM permissions"))
    connection.execute(sa.text("DELETE FROM actions"))

    # 3. Insert actions based on Actions enum
    actions = [action.value for action in Actions]
    action_ids: dict[str, str] = {}
    for action in actions:
        action_ids[action] = str(uuid.uuid4())

    action_data = [
        {
            'id': action_ids[action],
            'name': action,
            'created_at': now,
            'updated_at': now,
        }
        for action in actions
    ]

    op.bulk_insert(
        sa.table(
            'actions',
            sa.Column('id', sa.UUID()),
            sa.Column('name', sa.String(50)),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        ),
        action_data
    )

    # 4. Build permissions for each existing feature x action
    features = connection.execute(
        sa.text("SELECT id, name FROM features")).fetchall()
    if not features:
        # No features to create permissions for
        return

    permission_data: list[dict] = []
    for feature_row in features:
        feature_id = feature_row[0]
        for action in actions:
            permission_data.append({
                'id': str(uuid.uuid4()),
                'feature_id': feature_id,
                'action_id': action_ids[action],
                'created_at': now,
                'updated_at': now,
            })

    op.bulk_insert(
        sa.table(
            'permissions',
            sa.Column('id', sa.UUID()),
            sa.Column('feature_id', sa.UUID()),
            sa.Column('action_id', sa.UUID()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        ),
        permission_data
    )


def downgrade() -> None:
    """Remove permissions and actions created by this migration.

    Note: downgrading will remove permissions and actions but cannot restore
    previously deleted associations or prior action/permission ids.
    """
    connection = op.get_bind()

    connection.execute(sa.text("DELETE FROM user_permissions"))
    connection.execute(sa.text("DELETE FROM permissions"))
    connection.execute(sa.text("DELETE FROM actions"))
