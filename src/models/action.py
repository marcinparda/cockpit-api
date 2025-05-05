from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from sqlalchemy.orm import relationship

class Action(BaseModel):
    __tablename__ = 'actions'
    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default='gen_random_uuid()')
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', back_populates='action')
