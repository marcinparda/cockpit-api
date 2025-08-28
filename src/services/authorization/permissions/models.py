"""Permission system core models."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.common.models import BaseModel


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