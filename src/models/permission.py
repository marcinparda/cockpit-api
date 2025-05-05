from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel
from sqlalchemy.orm import relationship


class Permission(BaseModel):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)

    api_keys = relationship('APIKeyPermission', back_populates='permission')
