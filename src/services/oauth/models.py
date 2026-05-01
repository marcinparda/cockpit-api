from datetime import datetime
from typing import Optional
from uuid import UUID as UUIDType

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.common.models import BaseModel


class OAuthClient(BaseModel):
    __tablename__ = "oauth_clients"

    id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                         server_default=text('gen_random_uuid()'), init=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True,
                                            index=True, init=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, init=False)
    redirect_uris: Mapped[str] = mapped_column(Text, nullable=False, init=False)
    grant_types: Mapped[str] = mapped_column(String(255), nullable=False,
                                              default="authorization_code", init=False)
    response_types: Mapped[str] = mapped_column(String(255), nullable=False,
                                                 default="code", init=False)
    token_endpoint_auth_method: Mapped[str] = mapped_column(String(50), nullable=False,
                                                              default="none", init=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, init=False)


class OAuthAuthorizationCode(BaseModel):
    __tablename__ = "oauth_authorization_codes"

    id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                         server_default=text('gen_random_uuid()'), init=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True,
                                       index=True, init=False)
    client_id: Mapped[str] = mapped_column(String(255),
                                            ForeignKey("oauth_clients.client_id", ondelete="CASCADE"),
                                            nullable=False, index=True, init=False)
    user_id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True),
                                               ForeignKey("users.id", ondelete="CASCADE"),
                                               nullable=False, index=True, init=False)
    redirect_uri: Mapped[str] = mapped_column(String(2048), nullable=False, init=False)
    scope: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True,
                                                  default=None, init=False)
    code_challenge: Mapped[str] = mapped_column(String(255), nullable=False, init=False)
    code_challenge_method: Mapped[str] = mapped_column(String(10), nullable=False,
                                                        default="S256", init=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, init=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, init=False)


class OAuthAccessToken(BaseModel):
    __tablename__ = "oauth_access_tokens"

    id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                         server_default=text('gen_random_uuid()'), init=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True,
                                        index=True, init=False)
    client_id: Mapped[str] = mapped_column(String(255),
                                            ForeignKey("oauth_clients.client_id", ondelete="CASCADE"),
                                            nullable=False, index=True, init=False)
    user_id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True),
                                               ForeignKey("users.id", ondelete="CASCADE"),
                                               nullable=False, index=True, init=False)
    scope: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True,
                                                  default=None, init=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, init=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, init=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True,
                                                              default=None, init=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True,
                                                          unique=True, index=True,
                                                          default=None, init=False)
    refresh_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True,
                                                                          default=None, init=False)
    refresh_token_is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                            default=False, init=False)
