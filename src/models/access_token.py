from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class AccessToken(BaseModel):
    """Access token model for JWT token tracking."""

    __tablename__ = "access_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default=text('gen_random_uuid()'))
    jti = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # Relationship to user
    user = relationship("User", back_populates="access_tokens")

    __table_args__ = (
        Index('idx_access_tokens_user_expires', 'user_id', 'expires_at'),
        Index('idx_access_tokens_jti_revoked', 'jti', 'is_revoked'),
    )

    def __repr__(self) -> str:
        return f"<AccessToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
