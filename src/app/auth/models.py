"""Authentication and authorization models."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID as UUIDType
import uuid

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, UniqueConstraint,
    DateTime, text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import BaseModel

if TYPE_CHECKING:
    pass


class UserRole(BaseModel):
    """User role model for role-based access control."""

    __tablename__ = "user_roles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationship with users
    users = relationship("User", back_populates="role")


class Action(BaseModel):
    """Action model for permission system."""
    __tablename__ = 'actions'
    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='gen_random_uuid()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='action')


class Feature(BaseModel):
    """Feature model for permission system."""
    __tablename__ = 'features'
    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='gen_random_uuid()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='feature')


class Permission(BaseModel):
    """Permission model linking features and actions."""
    __tablename__ = "permissions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "features.id"), nullable=False)
    action_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "actions.id"), nullable=False)

    # Relationships
    feature = relationship('Feature', back_populates='permissions')
    action = relationship('Action', back_populates='permissions')
    users = relationship('UserPermission', back_populates='permission')


class UserPermission(BaseModel):
    """Junction table for user permissions."""

    __tablename__ = "user_permissions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    permission_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "permissions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="users")

    # Unique constraint to prevent duplicate user-permission combinations
    __table_args__ = (UniqueConstraint(
        'user_id', 'permission_id', name='uix_user_permission'),)

    def __repr__(self) -> str:
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id})>"


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role_id = Column(PG_UUID(as_uuid=True), ForeignKey(
        "user_roles.id"), nullable=False)
    password_changed = Column(Boolean, default=False, nullable=False)
    created_by = Column(PG_UUID(as_uuid=True),
                        ForeignKey("users.id"), nullable=True)

    # Relationships
    role = relationship("UserRole", back_populates="users")
    permissions = relationship(
        "UserPermission", back_populates="user", cascade="all, delete-orphan")
    access_tokens = relationship(
        "AccessToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan")
    todo_projects = relationship(
        "TodoProject", back_populates="owner", cascade="all, delete-orphan")
    todo_collaborations = relationship(
        "TodoProjectCollaborator", back_populates="user", cascade="all, delete-orphan")

    # Self-referential relationship for created_by
    creator = relationship("User", remote_side=[id], backref="created_users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"


class AccessToken(BaseModel):
    """Access token model for JWT token tracking."""

    __tablename__ = "access_tokens"

    # Mark all fields with init=False to avoid dataclass initialization issues
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
    user: Mapped["User"] = relationship(
        "User", back_populates="access_tokens", init=False)

    def __repr__(self) -> str:
        return f"<AccessToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"


class RefreshToken(BaseModel):
    """Refresh token model for JWT refresh token tracking."""

    __tablename__ = "refresh_tokens"

    # Mark all fields with init=False to avoid dataclass initialization issues
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
    user: Mapped["User"] = relationship(
        "User", back_populates="refresh_tokens", init=False)

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, jti={self.jti}, user_id={self.user_id}, is_revoked={self.is_revoked})>"