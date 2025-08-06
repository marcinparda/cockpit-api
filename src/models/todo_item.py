from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class TodoItem(BaseModel):
    __tablename__ = "todo_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_closed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    shops = Column(String(255), nullable=True)
    project_id = Column(Integer, ForeignKey(
        "todo_projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("TodoProject", back_populates="items")
