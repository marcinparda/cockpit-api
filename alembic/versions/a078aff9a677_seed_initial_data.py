"""Seed initial data

Revision ID: a078aff9a677
Revises: 6cce1c565859
Create Date: 2025-05-03 15:01:10.554014

"""
from typing import Sequence, Union
import uuid
import secrets
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from src.app.auth.enums.actions import Actions
from src.app.auth.enums.features import Features


# revision identifiers, used by Alembic.
revision: str = 'a078aff9a677'
down_revision: Union[str, None] = '6cce1c565859'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial data for all tables."""
    # Get current timestamp
    now = datetime.now()

    # 1. Insert initial payment methods
    payment_methods = sa.table(
        'payment_methods',
        sa.column('name', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    op.bulk_insert(payment_methods, [
        {'name': 'Cash', 'created_at': now, 'updated_at': now},
    ])

    # 2. Insert features
    features = [feature.value for feature in Features]
    feature_ids = {}
    for feature in features:
        feature_id = str(uuid.uuid4())
        feature_ids[feature] = feature_id

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

    # 3. Insert actions
    actions = [action.value for action in Features]
    action_ids = {}
    for action in actions:
        action_id = str(uuid.uuid4())
        action_ids[action] = action_id

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

    # 4. Insert permissions
    permission_ids = {}
    permission_data = []
    for feature in features:
        for action in actions:
            permission_id = str(uuid.uuid4())
            permission_ids[(feature, action)] = permission_id
            permission_data.append({
                'id': permission_id,
                'feature_id': feature_ids[feature],
                'action_id': action_ids[action],
                'created_at': now,
                'updated_at': now
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

    # 5. Create admin API key
    connection = op.get_bind()

    # Generate API key details
    api_key_string = secrets.token_urlsafe(32)
    api_key_id = str(uuid.uuid4())

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

    # 6. Associate all permissions with admin API key
    api_key_permission_data = [
        {
            'api_key_id': api_key_id,
            'permission_id': permission_id,
            'created_at': now,
            'updated_at': now
        }
        for permission_id in [p['id'] for p in permission_data]
    ]

    op.bulk_insert(
        sa.table(
            'api_key_permissions',
            sa.Column('api_key_id', sa.UUID()),
            sa.Column('permission_id', sa.UUID()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        ),
        api_key_permission_data
    )

    # Print the API key for initial setup
    print("\n\n============================================")
    print(f"Created Admin API Key: {api_key_string}")
    print("Please store this key safely, it won't be shown again.")
    print("============================================\n\n")


def downgrade() -> None:
    """Remove all seeded data."""
    # 1. Remove API key permissions
    op.execute("DELETE FROM api_key_permissions")

    # 2. Remove API keys
    op.execute("DELETE FROM api_keys")

    # 3. Remove permissions
    op.execute("DELETE FROM permissions")

    # 4. Remove actions
    op.execute("DELETE FROM actions")

    # 5. Remove features
    op.execute("DELETE FROM features")

    # 6. Remove payment methods
    op.execute("DELETE FROM payment_methods WHERE name = 'Cash'")
