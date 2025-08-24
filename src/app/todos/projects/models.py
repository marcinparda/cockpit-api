from datetime import datetime
from uuid import UUID as UUID_T
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

if TYPE_CHECKING:
    from src.app.todos.items.models import TodoItem
    from src.app.auth.models import User
    from src.app.todos.collaborators.models import TodoProjectCollaborator


class TodoProject(Base):
    __tablename__ = "todo_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    owner_id: Mapped[UUID_T] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    items: Mapped[list["TodoItem"]] = relationship(
        "TodoItem", back_populates="project", cascade="all, delete-orphan")
    owner: Mapped["User"] = relationship(
        "User", back_populates="todo_projects")
    collaborators: Mapped[list["TodoProjectCollaborator"]] = relationship(
        "TodoProjectCollaborator", back_populates="project", cascade="all, delete-orphan")

    is_general: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
