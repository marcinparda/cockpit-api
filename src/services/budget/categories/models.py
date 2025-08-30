"""Category model for expense categorization with hierarchical support."""

from typing import Optional
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.common.models import BaseModel


class Category(BaseModel):
    """Category model for expense categorization with hierarchical support."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=None)
    name: Mapped[str] = mapped_column(nullable=False, default="")
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True, default=None)

    # Self-referential relationship
    children = relationship("Category", back_populates="parent")
    parent = relationship("Category", remote_side=[
                          id], back_populates="children")

    # Relationship with expenses
    expenses = relationship("Expense", back_populates="category")

    # For leaf node validation
    @property
    def is_leaf(self):
        return not self.children