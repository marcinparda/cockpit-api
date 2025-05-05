from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


class APIKeyPermission(BaseModel):
    __tablename__ = 'api_key_permissions'

    api_key_id = Column(UUID(as_uuid=True), ForeignKey(
        'api_keys.id'), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey(
        'permissions.id'), primary_key=True)

    api_key = relationship('APIKey', back_populates='permissions')
    permission = relationship('Permission', back_populates='api_keys')
