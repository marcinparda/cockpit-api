"""Add OAuth tables for MCP Authorization Code flow

Revision ID: b2c3d4e5f6a7
Revises: f9c1d2e3f4a5
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Tuple, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Tuple[str, ...], None] = ('a1b2c3d4e5f6', '4f4676dedb5d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'oauth_clients',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('redirect_uris', sa.Text(), nullable=False),
        sa.Column('grant_types', sa.String(255), nullable=False),
        sa.Column('response_types', sa.String(255), nullable=False),
        sa.Column('token_endpoint_auth_method', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_oauth_clients_client_id', 'oauth_clients', ['client_id'], unique=True)

    op.create_table(
        'oauth_authorization_codes',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('redirect_uri', sa.String(2048), nullable=False),
        sa.Column('scope', sa.String(1024), nullable=True),
        sa.Column('code_challenge', sa.String(255), nullable=False),
        sa.Column('code_challenge_method', sa.String(10), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.client_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_oauth_authorization_codes_code', 'oauth_authorization_codes',
                    ['code'], unique=True)
    op.create_index('ix_oauth_authorization_codes_client_id', 'oauth_authorization_codes',
                    ['client_id'])
    op.create_index('ix_oauth_authorization_codes_user_id', 'oauth_authorization_codes',
                    ['user_id'])
    op.create_index('ix_oauth_authorization_codes_expires_at', 'oauth_authorization_codes',
                    ['expires_at'])

    op.create_table(
        'oauth_access_tokens',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope', sa.String(1024), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('refresh_token', sa.String(255), nullable=True),
        sa.Column('refresh_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('refresh_token_is_revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.client_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_oauth_access_tokens_token', 'oauth_access_tokens', ['token'], unique=True)
    op.create_index('ix_oauth_access_tokens_client_id', 'oauth_access_tokens', ['client_id'])
    op.create_index('ix_oauth_access_tokens_user_id', 'oauth_access_tokens', ['user_id'])
    op.create_index('ix_oauth_access_tokens_expires_at', 'oauth_access_tokens', ['expires_at'])
    op.create_index('ix_oauth_access_tokens_refresh_token', 'oauth_access_tokens',
                    ['refresh_token'], unique=True)


def downgrade() -> None:
    op.drop_table('oauth_access_tokens')
    op.drop_table('oauth_authorization_codes')
    op.drop_table('oauth_clients')
