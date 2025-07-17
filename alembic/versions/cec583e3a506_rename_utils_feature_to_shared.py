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
    """Rename utils feature to shared."""
    # Update the feature name from 'utils' to 'shared'
    op.execute("UPDATE features SET name = 'shared' WHERE name = 'utils'")


def downgrade() -> None:
    """Revert shared feature name back to utils."""
    # Revert the feature name from 'shared' back to 'utils'
    op.execute("UPDATE features SET name = 'utils' WHERE name = 'shared'")
