"""remove_agent_service

Revision ID: 559981a05f16
Revises: a1b2c3d4e5f6
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '559981a05f16'
down_revision: Union[str, None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FEATURE_NAME = "agent"


def upgrade() -> None:
    connection = op.get_bind()

    op.drop_index('ix_agent_messages_conversation_id', table_name='agent_messages')
    op.drop_table('agent_messages')
    op.drop_index('ix_agent_conversations_user_id', table_name='agent_conversations')
    op.drop_table('agent_conversations')

    feature_row = connection.execute(
        sa.text("SELECT id FROM features WHERE name = :name"),
        {"name": FEATURE_NAME},
    ).fetchone()
    if feature_row is None:
        return
    feature_id = feature_row[0]

    perm_ids = [r[0] for r in connection.execute(
        sa.text("SELECT id FROM permissions WHERE feature_id = :fid"),
        {"fid": feature_id},
    ).fetchall()]

    for pid in perm_ids:
        connection.execute(sa.text("DELETE FROM user_permissions WHERE permission_id = :pid"), {"pid": pid})

    connection.execute(sa.text("DELETE FROM permissions WHERE feature_id = :fid"), {"fid": feature_id})
    connection.execute(sa.text("DELETE FROM features WHERE id = :fid"), {"fid": feature_id})


def downgrade() -> None:
    from datetime import datetime
    from uuid import uuid4

    connection = op.get_bind()

    op.create_table(
        'agent_conversations',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_conversations_user_id', 'agent_conversations', ['user_id'])

    op.create_table(
        'agent_messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['agent_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_messages_conversation_id', 'agent_messages', ['conversation_id'])

    now = datetime.now()
    feature_id = str(uuid4())
    connection.execute(
        sa.text("INSERT INTO features (id, name, created_at, updated_at) VALUES (:id, :name, :created_at, :updated_at)"),
        {"id": feature_id, "name": FEATURE_NAME, "created_at": now, "updated_at": now},
    )

    for action_name in ["create", "read", "update", "delete"]:
        action_row = connection.execute(
            sa.text("SELECT id FROM actions WHERE name = :name"), {"name": action_name}
        ).fetchone()
        if action_row is None:
            continue
        connection.execute(
            sa.text("INSERT INTO permissions (id, feature_id, action_id, created_at, updated_at) VALUES (:id, :fid, :aid, :created_at, :updated_at)"),
            {"id": str(uuid4()), "fid": feature_id, "aid": action_row[0], "created_at": now, "updated_at": now},
        )
