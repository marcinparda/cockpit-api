from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from src.core.database import get_db
from src.models.payment_method import PaymentMethod as PaymentMethodModel
from src.schemas.payment_method import PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate
from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_payment_methods_permissions

router = APIRouter()


@router.get("/", response_model=list[PaymentMethod])
async def list_payment_methods(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.READ))
):
    result = await db.execute(select(PaymentMethodModel))
    return result.scalars().all()


@router.post("/", response_model=PaymentMethod, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_method: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.CREATE))
):
    now = datetime.now()
    db_payment_method = PaymentMethodModel(
        **payment_method.dict(),
        created_at=now,
        updated_at=now
    )
    db.add(db_payment_method)
    await db.commit()
    await db.refresh(db_payment_method)
    return db_payment_method


@router.get("/{payment_method_id}", response_model=PaymentMethod)
async def get_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.READ))
):
    payment_method = await db.get(PaymentMethodModel, payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Payment method not found")
    return payment_method


@router.put("/{payment_method_id}", response_model=PaymentMethod)
async def update_payment_method(
    payment_method_id: int,
    payment_method_update: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.UPDATE))
):
    payment_method = await db.get(PaymentMethodModel, payment_method_id)
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    update_data = payment_method_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(payment_method, key, value)

    payment_method.updated_at = datetime.now()
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


@router.delete("/{payment_method_id}", status_code=204)
async def delete_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.DELETE))
):
    payment_method = await db.get(PaymentMethodModel, payment_method_id)
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    await db.delete(payment_method)
    await db.commit()
