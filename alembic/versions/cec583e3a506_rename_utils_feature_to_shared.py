"""rename_utils_feature_to_shared

Revision ID: cec583e3a506
Revises: f8f54e6ca6b7
Create Date: 2025-07-17 10:21:18.286482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cec583e3a506'
down_revision: Union[str, None] = 'f8f54e6ca6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename utils feature to shared safely."""
    # Update the feature name from 'utils' to 'shared' only if 'shared' does not already exist
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS(SELECT 1 FROM features WHERE name = 'utils') THEN
        IF NOT EXISTS(SELECT 1 FROM features WHERE name = 'shared') THEN
          UPDATE features SET name = 'shared' WHERE name = 'utils';
        END IF;
      END IF;
    END
    $$;
    """)


def downgrade() -> None:
    """Revert shared feature name back to utils if appropriate."""
    # Revert the feature name from 'shared' back to 'utils' only if 'utils' does not already exist
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS(SELECT 1 FROM features WHERE name = 'shared') THEN
        IF NOT EXISTS(SELECT 1 FROM features WHERE name = 'utils') THEN
          UPDATE features SET name = 'utils' WHERE name = 'shared';
        END IF;
      END IF;
    END
    $$;
    """)
