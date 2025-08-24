from uuid import UUID as UUID_T
from typing import Optional
from sqlalchemy import Integer, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.app.todos.projects.models import TodoProject
from src.app.auth.models import User

from src.common.models import BaseModel


class TodoProjectCollaborator(BaseModel):
    __tablename__ = "todo_project_collaborators"

    project_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "todo_projects.id", ondelete="CASCADE"), primary_key=True, default=None)
    user_id: Mapped[UUID_T] = mapped_column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True, default=None)

    project: Mapped["TodoProject"] = relationship(
        "TodoProject", back_populates="collaborators", default=None)
    user: Mapped["User"] = relationship(
        "User", back_populates="todo_collaborations", default=None)

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id',
                         name='unique_project_user_collaboration'),
    )
