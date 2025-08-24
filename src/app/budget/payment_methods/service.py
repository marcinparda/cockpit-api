"""Payment method service for payment method management operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from datetime import datetime

from src.app.budget.models import PaymentMethod
from .schemas import PaymentMethodCreate, PaymentMethodUpdate


async def get_payment_method_by_id(db: AsyncSession, payment_method_id: int) -> Optional[PaymentMethod]:
    """
    Get payment method by ID.

    Args:
        db: Database session
        payment_method_id: Payment method ID

    Returns:
        PaymentMethod object if found, None otherwise
    """
    return await db.get(PaymentMethod, payment_method_id)


async def get_all_payment_methods(db: AsyncSession) -> Sequence[PaymentMethod]:
    """
    Get all payment methods.

    Args:
        db: Database session

    Returns:
        Sequence of all payment methods
    """
    result = await db.execute(select(PaymentMethod))
    return result.scalars().all()


async def create_payment_method(
    db: AsyncSession,
    payment_method_data: PaymentMethodCreate
) -> PaymentMethod:
    """
    Create a new payment method.

    Args:
        db: Database session
        payment_method_data: Payment method creation data

    Returns:
        Created PaymentMethod object
    """
    now = datetime.now()
    payment_method = PaymentMethod(
        **payment_method_data.model_dump(),
        created_at=now,
        updated_at=now
    )
    db.add(payment_method)
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


async def update_payment_method(
    db: AsyncSession,
    payment_method_id: int,
    payment_method_data: PaymentMethodUpdate
) -> Optional[PaymentMethod]:
    """
    Update an existing payment method.

    Args:
        db: Database session
        payment_method_id: Payment method ID
        payment_method_data: Updated payment method data

    Returns:
        Updated PaymentMethod object, None if not found
    """
    payment_method = await get_payment_method_by_id(db, payment_method_id)
    if not payment_method:
        return None

    update_data = payment_method_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(payment_method, key, value)

    payment_method.updated_at = datetime.now()
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


async def delete_payment_method(db: AsyncSession, payment_method_id: int) -> bool:
    """
    Delete a payment method.

    Args:
        db: Database session
        payment_method_id: Payment method ID

    Returns:
        True if payment method was deleted, False if not found
    """
    payment_method = await get_payment_method_by_id(db, payment_method_id)
    if not payment_method:
        return False

    await db.delete(payment_method)
    await db.commit()
    return True
