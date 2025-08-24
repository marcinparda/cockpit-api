"""Budget management models for expenses, categories, and payment methods."""

from datetime import date as date_type, datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Numeric, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.common.models import BaseModel
from src.core.database import Base


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


class PaymentMethod(Base):
    """Payment method model for tracking how expenses were paid."""
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationship to expenses (if you want backref)
    expenses = relationship("Expense", back_populates="payment_method")


class Expense(BaseModel):
    """Expense model for tracking individual expenses."""
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, default=None)
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0)
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True, default=None)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), default=None)
    category = relationship("Category", back_populates="expenses")

    payment_method_id: Mapped[int] = mapped_column(
        ForeignKey("payment_methods.id"), default=None)
    payment_method = relationship("PaymentMethod", back_populates="expenses")

    date: Mapped[date_type] = mapped_column(Date, default=date_type.today())