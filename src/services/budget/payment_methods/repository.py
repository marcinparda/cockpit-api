"""Payment method repository for database operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.services.budget.payment_methods.models import PaymentMethod


async def get_payment_method_by_id(db: AsyncSession, payment_method_id: int) -> Optional[PaymentMethod]:
    """Get payment method by ID."""
    return await db.get(PaymentMethod, payment_method_id)


async def get_all_payment_methods(db: AsyncSession) -> Sequence[PaymentMethod]:
    """Get all payment methods."""
    result = await db.execute(select(PaymentMethod))
    return result.scalars().all()


async def save_payment_method(db: AsyncSession, payment_method: PaymentMethod) -> PaymentMethod:
    """Save payment method to database."""
    db.add(payment_method)
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


async def update_payment_method(db: AsyncSession, payment_method: PaymentMethod) -> PaymentMethod:
    """Update payment method in database."""
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


async def delete_payment_method_record(db: AsyncSession, payment_method: PaymentMethod) -> None:
    """Delete payment method record from database."""
    await db.delete(payment_method)
    await db.commit()