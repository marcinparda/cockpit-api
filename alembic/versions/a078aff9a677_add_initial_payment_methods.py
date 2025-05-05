"""Add initial payment methods

Revision ID: a078aff9a677
Revises: 6cce1c565859
Create Date: 2025-05-03 15:01:10.554014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'a078aff9a677'
down_revision: Union[str, None] = '6cce1c565859'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    payment_methods = sa.table(
        'payment_methods',
        sa.column('name', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    op.bulk_insert(payment_methods, [
        {'name': 'Cash', 'created_at': datetime(
            2025, 5, 1), 'updated_at': datetime(2025, 5, 1)},
    ])


def downgrade():
    op.execute(
        "DELETE FROM payment_methods WHERE name IN ('Credit Card', 'Cash', 'Bank Transfer')"
    )
