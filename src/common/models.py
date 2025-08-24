"""Shared base models and mixins for all domain models."""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model class with timestamps for all domain models."""
    __abstract__ = True