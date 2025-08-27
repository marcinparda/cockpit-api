"""Authentication models for JWT tokens."""

from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship

from src.common.models import BaseTokenModel

if TYPE_CHECKING:
    from src.app.users.models import User


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
