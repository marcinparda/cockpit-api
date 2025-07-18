from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey(
        "user_roles.id"), nullable=False)
    password_changed = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True),
                        ForeignKey("users.id"), nullable=True)

    # Relationships
    role = relationship("UserRole", back_populates="users")
    permissions = relationship(
        "UserPermission", back_populates="user", cascade="all, delete-orphan")

    # Self-referential relationship for created_by
    creator = relationship("User", remote_side=[id], backref="created_users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
