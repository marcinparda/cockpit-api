"""Permission system core models."""

from uuid import UUID
from typing import List
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import BaseModel
from src.services.authorization.user_permissions.models import UserPermission


class Action(BaseModel):
    """Action model for permission system."""
    __tablename__ = 'actions'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()'
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    permissions: Mapped[List["Permission"]] = relationship(
        'Permission', back_populates='action')


class Feature(BaseModel):
    """Feature model for permission system."""
    __tablename__ = 'features'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()'
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    permissions: Mapped[List["Permission"]] = relationship(
        'Permission', back_populates='feature')


class Permission(BaseModel):
    """Permission model linking features and actions."""
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()'
    )
    feature_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("features.id"), nullable=False
    )
    action_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("actions.id"), nullable=False
    )

    # Relationships
    feature: Mapped["Feature"] = relationship(
        'Feature', back_populates='permissions')
    action: Mapped["Action"] = relationship(
        'Action', back_populates='permissions')
    users: Mapped[List["UserPermission"]] = relationship(
        'UserPermission', back_populates='permission')
