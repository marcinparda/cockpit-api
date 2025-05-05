from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from sqlalchemy.orm import relationship

class Feature(BaseModel):
    __tablename__ = 'features'
    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default='gen_random_uuid()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='feature')
