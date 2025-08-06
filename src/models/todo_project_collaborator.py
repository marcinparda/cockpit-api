from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class TodoProjectCollaborator(BaseModel):
    __tablename__ = "todo_project_collaborators"

    project_id = Column(Integer, ForeignKey(
        "todo_projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    project = relationship("TodoProject", back_populates="collaborators")
    user = relationship("User", back_populates="todo_collaborations")

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id',
                         name='unique_project_user_collaboration'),
    )
