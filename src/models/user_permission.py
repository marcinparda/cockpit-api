from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserPermission(BaseModel):
    """Junction table for user permissions."""

    __tablename__ = "user_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey(
        "permissions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="users")

    # Unique constraint to prevent duplicate user-permission combinations
    __table_args__ = (UniqueConstraint(
        'user_id', 'permission_id', name='uix_user_permission'),)

    def __repr__(self) -> str:
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id})>"
