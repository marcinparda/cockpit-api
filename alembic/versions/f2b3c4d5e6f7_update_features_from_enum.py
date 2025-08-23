"""Update features table from Features enum

Revision ID: f2b3c4d5e6f7
Revises: e9a1c3b2d4f5
Create Date: 2025-08-21 12:30:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from sqlalchemy.sql import text
from src.app.auth.enums.features import Features


# revision identifiers, used by Alembic.
revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, None] = 'e9a1c3b2d4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sync the features table with the `Features` enum.

    - Inserts missing features (generates new UUIDs)
    - Removes features that are no longer present in the enum (and related
      permissions and permission associations)
    """
    connection = op.get_bind()
    now = datetime.now()

    # Load current features from DB
    try:
        rows = connection.execute(
            sa.text("SELECT id, name FROM features")).fetchall()
    except sa_exc.ProgrammingError:
        # features table does not exist in some environments
        print("features table not present, skipping features sync")
        return

    db_features = {row[1]: str(row[0]) for row in rows}
    enum_features = [f.value for f in Features]

    to_add = [f for f in enum_features if f not in db_features]
    to_remove = [name for name in db_features.keys()
                 if name not in enum_features]

    # 1. Remove features not present in enum (and cascade-clean associated permissions)
    def table_exists(table_name: str) -> bool:
        result = connection.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :t)"
            ),
            {"t": table_name}
        ).fetchone()
        return bool(result[0]) if result is not None else False

    for name in to_remove:
        feature_id = db_features[name]

        # delete api_key_permissions referencing permissions for this feature
        if table_exists('api_key_permissions') and table_exists('permissions'):
            connection.execute(sa.text(
                "DELETE FROM api_key_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE feature_id = :feature_id)"
            ), {"feature_id": feature_id})
        else:
            print("api_key_permissions or permissions table not present, skipping api_key_permissions cleanup for feature: ", name)

        # delete user_permissions referencing permissions for this feature
        if table_exists('user_permissions') and table_exists('permissions'):
            connection.execute(sa.text(
                "DELETE FROM user_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE feature_id = :feature_id)"
            ), {"feature_id": feature_id})
        else:
            print("user_permissions or permissions table not present, skipping user_permissions cleanup for feature: ", name)

        # delete permissions for this feature
        if table_exists('permissions'):
            connection.execute(sa.text(
                "DELETE FROM permissions WHERE feature_id = :feature_id"
            ), {"feature_id": feature_id})
        else:
            print(
                "permissions table not present, skipping permissions deletion for feature: ", name)

        # delete feature
        if table_exists('features'):
            connection.execute(sa.text(
                "DELETE FROM features WHERE id = :feature_id"
            ), {"feature_id": feature_id})
            print(f"Removed feature '{name}' and related permissions")
        else:
            print(f"features table not present, skipping removal of '{name}'")

    # 2. Insert new features from enum
    if to_add:
        feature_ids = {name: str(uuid.uuid4()) for name in to_add}
        feature_data = [
            {
                'id': feature_ids[name],
                'name': name,
                'created_at': now,
                'updated_at': now,
            }
            for name in to_add
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

        print(f"Inserted features: {to_add}")


def downgrade() -> None:
    """Downgrade not supported: this migration syncs DB features with code enum.

    Rolling back could remove or re-add rows that previous versions relied on.
    Keep downgrade empty to avoid accidental destructive changes.
    """
    pass
