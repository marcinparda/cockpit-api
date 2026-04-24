"""drop deprecated budget and todos tables

Revision ID: a2b3c4d5e6f7
Revises: 901cfdcb8a1d
Create Date: 2026-04-24

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '901cfdcb8a1d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove permissions for deprecated features
    op.execute(
        """
        DELETE FROM user_permissions
        WHERE permission_id IN (
            SELECT p.id FROM permissions p
            JOIN features f ON p.feature_id = f.id
            WHERE f.name IN ('categories', 'expenses', 'payment_methods', 'todo_items')
        )
        """
    )
    op.execute(
        """
        DELETE FROM permissions
        WHERE feature_id IN (
            SELECT id FROM features
            WHERE name IN ('categories', 'expenses', 'payment_methods', 'todo_items')
        )
        """
    )
    op.execute(
        """
        DELETE FROM features
        WHERE name IN ('categories', 'expenses', 'payment_methods', 'todo_items')
        """
    )

    # Drop todos tables (order matters due to FK constraints)
    op.drop_table('todo_project_collaborators')
    op.drop_table('todo_items')
    op.drop_table('todo_projects')

    # Drop budget tables
    op.drop_table('expenses')
    op.drop_table('categories')
    op.drop_table('payment_methods')


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
