from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class TodoProject(Base):
    __tablename__ = "todo_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
