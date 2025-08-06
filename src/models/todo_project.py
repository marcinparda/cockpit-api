from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TodoProject(Base):
    __tablename__ = "todo_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    is_general = Column(Boolean, default=False, nullable=False)

    # Relationships
    items = relationship("TodoItem", back_populates="project",
                         cascade="all, delete-orphan")
    owner = relationship("User", back_populates="todo_projects")
    collaborators = relationship(
        "TodoProjectCollaborator", back_populates="project", cascade="all, delete-orphan")
