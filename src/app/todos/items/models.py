from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.models import BaseModel

if TYPE_CHECKING:
    from src.app.todos.projects.models import TodoProject


class TodoItem(BaseModel):
    __tablename__ = "todo_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, init=False)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, default="")

    project_id: Mapped[int] = mapped_column(ForeignKey(
        "todo_projects.id", ondelete="CASCADE"), nullable=False, default=None)
    project: Mapped["TodoProject"] = relationship(
        back_populates="items", default=None)

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None)
    is_closed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None)
    shops: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None)
