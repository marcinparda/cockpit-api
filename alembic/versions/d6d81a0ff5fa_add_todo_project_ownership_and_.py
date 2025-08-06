"""add_todo_project_ownership_and_collaboration

Revision ID: d6d81a0ff5fa
Revises: 3a778cea0867
Create Date: 2025-08-06 18:55:27.660808

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd6d81a0ff5fa'
down_revision: Union[str, None] = '3a778cea0867'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema and migrate data."""
    # Create todo_project_collaborators table
    op.create_table('todo_project_collaborators',
                    sa.Column('project_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False,
                              server_default=sa.text('now()')),
                    sa.Column('updated_at', sa.DateTime(), nullable=False,
                              server_default=sa.text('now()')),
                    sa.ForeignKeyConstraint(
                        ['project_id'], ['todo_projects.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(
                        ['user_id'], ['users.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('project_id', 'user_id'),
                    sa.UniqueConstraint('project_id', 'user_id',
                                        name='unique_project_user_collaboration')
                    )

    # Add columns to todo_projects with nullable=True initially
    with op.batch_alter_table('todo_projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.UUID(), nullable=True))
        batch_op.add_column(
            sa.Column('is_general', sa.Boolean(), server_default='false', nullable=False))
        batch_op.drop_constraint('todo_projects_name_key', type_='unique')

    # Get default owner ID (different for dev and prod)
    conn = op.get_bind()

    # Fallback to first admin user if specified email not found
    result = conn.execute(text("SELECT id FROM users LIMIT 1"))
    default_owner_row = result.fetchone()
    default_owner_id = default_owner_row[0] if default_owner_row else None

    # Set default owner for all existing todo_projects
    conn.execute(
        text(f"UPDATE todo_projects SET owner_id = '{default_owner_id}'"))

    # Create "General" projects for all users
    result = conn.execute(text("SELECT id, email FROM users"))
    users_data = result.fetchall()
    now = datetime.now().isoformat()

    general_projects = {}
    for user_row in users_data:
        user_id = user_row[0]
        email = user_row[1]

        # Check if user already has a project
        result = conn.execute(
            text(f"SELECT id FROM todo_projects WHERE owner_id = '{user_id}' LIMIT 1"))
        existing_project = result.fetchone()

        if not existing_project:
            # Create a "General" project for this user
            result = conn.execute(
                text(f"INSERT INTO todo_projects (name, created_at, updated_at, owner_id, is_general) "
                     f"VALUES ('General', '{now}', '{now}', '{user_id}', TRUE) RETURNING id")
            )
            new_project = result.fetchone()
            if new_project:
                general_projects[str(user_id)] = new_project[0]

    # Get all user's general projects for item assignments
    for user_row in users_data:
        user_id = user_row[0]
        user_id_str = str(user_id)

        if user_id_str not in general_projects:
            result = conn.execute(
                text(
                    f"SELECT id FROM todo_projects WHERE owner_id = '{user_id}' AND is_general = TRUE LIMIT 1")
            )
            general_project = result.fetchone()

            if general_project:
                general_projects[user_id_str] = general_project[0]

    # Assign orphaned items to owner's general project
    result = conn.execute(
        text("SELECT id FROM todo_items WHERE project_id IS NULL"))
    orphaned_items = result.fetchall()

    if orphaned_items and default_owner_id:
        # Make sure we have a General project for the default owner
        if str(default_owner_id) not in general_projects:
            # Create one if it doesn't exist
            result = conn.execute(
                text(
                    f"SELECT id FROM todo_projects WHERE owner_id = '{default_owner_id}' AND is_general = TRUE LIMIT 1")
            )
            general_project = result.fetchone()

            if general_project:
                general_projects[str(default_owner_id)] = general_project[0]
            else:
                # Create a new General project for the default owner
                result = conn.execute(
                    text(f"INSERT INTO todo_projects (name, created_at, updated_at, owner_id, is_general) "
                         f"VALUES ('General', '{now}', '{now}', '{default_owner_id}', TRUE) RETURNING id")
                )
                new_project = result.fetchone()
                if new_project:
                    general_projects[str(default_owner_id)] = new_project[0]

        # Assign to default owner's general project
        default_general_project = general_projects.get(str(default_owner_id))
        if default_general_project:
            for item_row in orphaned_items:
                item_id = item_row[0]
                conn.execute(
                    text(
                        f"UPDATE todo_items SET project_id = {default_general_project} WHERE id = {item_id}")
                )

    # Add the foreign key constraints
    with op.batch_alter_table('todo_projects', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['owner_id'], ['id'])
        batch_op.alter_column('owner_id', nullable=False)

    # Update todo_items foreign key to CASCADE and make project_id required
    with op.batch_alter_table('todo_items', schema=None) as batch_op:
        batch_op.drop_constraint(
            'todo_items_project_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'todo_projects', ['project_id'], [
                                    'id'], ondelete='CASCADE')
        batch_op.alter_column(
            'project_id', existing_type=sa.INTEGER(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert todo_items changes
    with op.batch_alter_table('todo_items', schema=None) as batch_op:
        batch_op.alter_column(
            'project_id', existing_type=sa.INTEGER(), nullable=True)
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('todo_items_project_id_fkey', 'todo_projects', [
                                    'project_id'], ['id'], ondelete='SET NULL')

    # Revert todo_projects changes
    with op.batch_alter_table('todo_projects', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_unique_constraint('todo_projects_name_key', ['name'])
        batch_op.drop_column('is_general')
        batch_op.drop_column('owner_id')

    # Drop the collaborators table
    op.drop_table('todo_project_collaborators')
