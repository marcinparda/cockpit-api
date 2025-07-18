from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserRole(BaseModel):
    """User role model for role-based access control."""

    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationship with users
    users = relationship("User", back_populates="role")
