from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from sqlalchemy.orm import relationship

class Permission(BaseModel):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey(
        "features.id"), nullable=False)
    action_id = Column(UUID(as_uuid=True), ForeignKey(
        "actions.id"), nullable=False)

    # Relationships
    feature = relationship('Feature', back_populates='permissions')
    action = relationship('Action', back_populates='permissions')
    api_keys = relationship('APIKeyPermission', back_populates='permission')
