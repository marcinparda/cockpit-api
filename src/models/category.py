from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class Category(BaseModel):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=True)

    # Self-referential relationship
    children = relationship("Category", back_populates="parent")
    parent = relationship("Category", remote_side=[
                          id], back_populates="children")

    # For leaf node validation
    @property
    def is_leaf(self):
        return not self.children
