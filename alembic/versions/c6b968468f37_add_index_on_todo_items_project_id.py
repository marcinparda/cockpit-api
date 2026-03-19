"""add_index_on_todo_items_project_id

Revision ID: c6b968468f37
Revises: 8650ef3eeec7
Create Date: 2025-09-07 22:40:42.980272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6b968468f37'
down_revision: Union[str, None] = '8650ef3eeec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add index on project_id for performance optimization
    with op.batch_alter_table('todo_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_todo_items_project_id'), ['project_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index on project_id
    with op.batch_alter_table('todo_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_todo_items_project_id'))
