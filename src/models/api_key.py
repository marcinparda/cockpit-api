from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from sqlalchemy.orm import relationship


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    # ID of creator API key
    created_by = Column(UUID(as_uuid=True), nullable=True)
    permissions = relationship('APIKeyPermission', back_populates='api_key')
