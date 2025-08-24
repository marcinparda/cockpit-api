from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from .schemas import PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate
from .service import (
    get_all_payment_methods,
    get_payment_method_by_id,
    create_payment_method,
    update_payment_method,
    delete_payment_method
)
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_payment_methods_permissions

router = APIRouter()


@router.get("", response_model=list[PaymentMethod])
async def list_payment_methods(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.READ))
):
    return await get_all_payment_methods(db)


@router.post("", response_model=PaymentMethod, status_code=status.HTTP_201_CREATED)
async def create_payment_method_endpoint(
    payment_method_data: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.CREATE))
):
    return await create_payment_method(db, payment_method_data)


@router.get("/{payment_method_id}", response_model=PaymentMethod)
async def get_payment_method(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.READ))
):
    payment_method = await get_payment_method_by_id(db, payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Payment method not found")
    return payment_method


@router.put("/{payment_method_id}", response_model=PaymentMethod)
async def update_payment_method_endpoint(
    payment_method_id: int,
    payment_method_data: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.UPDATE))
):
    payment_method = await update_payment_method(db, payment_method_id, payment_method_data)
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return payment_method


@router.delete("/{payment_method_id}", status_code=204)
async def delete_payment_method_endpoint(
    payment_method_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_payment_methods_permissions(Actions.DELETE))
):
    deleted = await delete_payment_method(db, payment_method_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
