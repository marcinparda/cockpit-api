from datetime import datetime
from typing import Optional, TYPE_CHECKING, ClassVar
from uuid import UUID
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class AccessToken(BaseModel):
    """Access token model for JWT token tracking."""

    __tablename__ = "access_tokens"

    # Mark all fields with init=False to avoid dataclass initialization issues
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                     server_default=text('gen_random_uuid()'), init=False)
    jti: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, init=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True, init=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, init=False)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True, init=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, init=False)
    user: Mapped["User"] = relationship(
        "User", back_populates="access_tokens", init=False)

    def __repr__(self) -> str:
        return f"<AccessToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
