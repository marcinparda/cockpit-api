"""Authentication models for JWT tokens."""

from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship

from src.common.models import BaseModel
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, String, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from src.services.users.models import User


class BaseTokenModel(BaseModel):
    """Abstract base model for JWT tokens with common fields and behavior."""
    __abstract__ = True

    id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                         server_default=text('gen_random_uuid()'), init=False)
    jti: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, init=False)
    user_id: Mapped[UUIDType] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True, init=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, init=False)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True, init=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, init=False)


class AccessToken(BaseTokenModel):
    """Access token model for JWT token tracking."""

    __tablename__ = "access_tokens"

    user: Mapped["User"] = relationship(
        "User", back_populates="access_tokens", init=False)

    def __repr__(self) -> str:
        return f"<AccessToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"


class RefreshToken(BaseTokenModel):
    """Refresh token model for JWT refresh token tracking."""

    __tablename__ = "refresh_tokens"

    user: Mapped["User"] = relationship(
        "User", back_populates="refresh_tokens", init=False)

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
