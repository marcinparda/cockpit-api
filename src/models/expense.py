from datetime import date as date_type
from sqlalchemy import ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class Expense(BaseModel):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, default=date_type.today())
    description: Mapped[str] = mapped_column(nullable=True)

    # Relationships
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category = relationship("Category", back_populates="expenses")

    payment_method_id: Mapped[int] = mapped_column(
        ForeignKey("payment_methods.id"))
    payment_method = relationship("PaymentMethod", back_populates="expenses")
