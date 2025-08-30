"""Role models for role-based access control."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.common.models import BaseModel

if TYPE_CHECKING:
    from src.services.users.models import User


class UserRole(BaseModel):
    """User role model for role-based access control."""

    __tablename__ = "user_roles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True,
                server_default='uuid_generate_v4()')
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationship with users
    users = relationship("User", back_populates="role")
