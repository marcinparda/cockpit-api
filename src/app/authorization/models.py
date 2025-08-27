"""Authorization models for role-based access control and permissions."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Column, String, ForeignKey, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.common.models import BaseModel

if TYPE_CHECKING:
    from src.app.users.models import User


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
                server_default='uuid_generate_v4()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='action')


class Feature(BaseModel):
    """Feature model for permission system."""
    __tablename__ = 'features'
    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='feature')


class Permission(BaseModel):
    """Permission model linking features and actions."""
    __tablename__ = "permissions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
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
