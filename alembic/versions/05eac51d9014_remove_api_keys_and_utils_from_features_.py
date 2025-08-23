"""remove api_keys and utils from features table

Revision ID: 05eac51d9014
Revises: d6d81a0ff5fa
Create Date: 2025-08-21 19:54:12.401729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05eac51d9014'
down_revision: Union[str, None] = 'd6d81a0ff5fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove 'api_keys' and 'utils' feature and related permissions"""
    op.execute("""
    DO $$
    BEGIN
      -- If api_key_permissions exists, remove references to permissions from both features
      IF to_regclass('api_key_permissions') IS NOT NULL THEN
        DELETE FROM api_key_permissions WHERE permission_id IN (
          SELECT id FROM permissions WHERE feature_id IN (
            SELECT id FROM features WHERE name IN ('api_keys','utils')
          )
        );
      END IF;

      -- If user_permissions exists, remove references to permissions from both features
      IF to_regclass('user_permissions') IS NOT NULL THEN
        DELETE FROM user_permissions WHERE permission_id IN (
          SELECT id FROM permissions WHERE feature_id IN (
            SELECT id FROM features WHERE name IN ('api_keys','utils')
          )
        );
      END IF;

      -- If permissions exists, remove permissions for both features
      IF to_regclass('permissions') IS NOT NULL THEN
        DELETE FROM permissions WHERE feature_id IN (
          SELECT id FROM features WHERE name IN ('api_keys','utils')
        );
      END IF;

      -- If features exists, remove the feature rows
      IF to_regclass('features') IS NOT NULL THEN
        DELETE FROM features WHERE name IN ('api_keys','utils');
      END IF;
    END
    $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "INSERT INTO features (id, name, created_at, updated_at) VALUES (gen_random_uuid(), 'api_keys', now(), now()) ON CONFLICT (name) DO NOTHING"
    )

    op.execute(
        "INSERT INTO features (id, name, created_at, updated_at) VALUES (gen_random_uuid(), 'utils', now(), now()) ON CONFLICT (name) DO NOTHING"
    )
