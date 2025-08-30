"""User models for user management."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.common.models import BaseModel

if TYPE_CHECKING:
    from src.services.authorization.roles.models import UserRole
    from src.services.authorization.user_permissions.models import UserPermission
    from src.services.authentication.tokens.models import AccessToken, RefreshToken
    from src.services.todos.projects.models import TodoProject
    from src.services.todos.collaborators.models import TodoProjectCollaborator


class User(BaseModel):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True,
                                     server_default=text('uuid_generate_v4()'), init=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(
        "user_roles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False)
    password_changed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True),
                                                       ForeignKey("users.id"), nullable=True, default=None)

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
