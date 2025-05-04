"""Create API keys table

Revision ID: 9593044e866a
Revises: a078aff9a677
Create Date: 2025-05-04 19:35:11.170761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9593044e866a'
down_revision: Union[str, None] = 'a078aff9a677'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(),
                  server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('api_keys')
