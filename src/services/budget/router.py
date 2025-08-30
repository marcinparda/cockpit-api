"""Main expenses router combining all expense-related sub-modules."""

from fastapi import APIRouter
from .expenses.router import router as expenses_router
from .categories.router import router as categories_router
from .payment_methods.router import router as payment_methods_router

router = APIRouter()

router.include_router(expenses_router, prefix="/expenses",
                      tags=["budget/expenses"])
router.include_router(
    categories_router, prefix="/categories", tags=["budget/categories"])
router.include_router(payment_methods_router,
                      prefix="/payment-methods", tags=["budget/payment-methods"])
