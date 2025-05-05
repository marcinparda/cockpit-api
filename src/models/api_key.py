from sqlalchemy import JSON, Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from src.permissions import Resources, Actions
from sqlalchemy.orm import relationship


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # ID of creator API key
    permissions = relationship('APIKeyPermission', back_populates='api_key')

    @classmethod
    def validate_permissions(cls, permissions: dict):
        for resource, actions in permissions.items():
            if resource not in Resources.__members__.values():
                raise ValueError(f"Invalid resource: {resource}")
            if not all(action in Actions.__members__.values() for action in actions):
                raise ValueError(f"Invalid actions for {resource}")
