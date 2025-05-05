"""Add permission seed data

Revision ID: 5e8a7b23f91c
Revises: 25109eb32f73
Create Date: 2025-05-06 10:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import select

# revision identifiers, used by Alembic.
revision: str = '5e8a7b23f91c'
down_revision: Union[str, None] = '25109eb32f73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add features, actions, and permissions."""
    # Define our features and actions
    features = ["api_keys", "categories", "expenses", "payment_methods"]
    actions = ["create", "read", "update", "delete"]

    # Get current timestamp for created_at and updated_at columns
    now = datetime.now()

    # Store feature IDs by name for later use
    feature_ids = {}
    for feature in features:
        feature_id = str(uuid4())
        feature_ids[feature] = feature_id

    # Insert features
    feature_data = [
        {'id': feature_ids[feature], 'name': feature,
         'created_at': now, 'updated_at': now}
        for feature in features
    ]
    op.bulk_insert(
        sa.table(
            'features',
            sa.Column('id', sa.UUID()),
            sa.Column('name', sa.String(50)),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        ),
        feature_data
    )

    # Store action IDs by name for later use
    action_ids = {}
    for action in actions:
        action_id = str(uuid4())
        action_ids[action] = action_id

    # Insert actions
    action_data = [
        {'id': action_ids[action], 'name': action,
         'created_at': now, 'updated_at': now}
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

    # Create all possible permissions (feature + action combinations)
    permission_data = [
        {'id': str(uuid4()), 'feature_id': feature_ids[feature], 'action_id': action_ids[action],
         'created_at': now, 'updated_at': now}
        for feature in features
        for action in actions
    ]
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
    """Remove all seed data."""
    # Delete all permissions
    op.execute("DELETE FROM api_key_permissions")
    op.execute("DELETE FROM permissions")
    op.execute("DELETE FROM features")
    op.execute("DELETE FROM actions")
