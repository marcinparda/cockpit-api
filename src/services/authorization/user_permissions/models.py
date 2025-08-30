"""User permission models."""

from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import BaseModel

if TYPE_CHECKING:
    from src.services.users.models import User
    from src.services.authorization.permissions.models import Permission


class UserPermission(BaseModel):
    """Junction table for user permissions."""

    __tablename__ = "user_permissions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                     server_default=text('uuid_generate_v4()'), init=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    permission_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="users")

    # Unique constraint to prevent duplicate user-permission combinations
    __table_args__ = (UniqueConstraint(
        'user_id', 'permission_id', name='uix_user_permission'),)

    def __repr__(self) -> str:
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id})>"