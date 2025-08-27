"""Shared base models and mixins for all domain models."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, func, String, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

if TYPE_CHECKING:
    from src.app.users.models import User


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model class with timestamps for all domain models."""
    __abstract__ = True


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