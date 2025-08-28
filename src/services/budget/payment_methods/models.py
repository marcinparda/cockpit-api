"""Payment method model for tracking how expenses were paid."""

from datetime import datetime
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


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