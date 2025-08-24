"""Main expenses router combining all expense-related sub-modules."""

from fastapi import APIRouter
from .expenses.router import router as expenses_router
from .categories.router import router as categories_router
from .payment_methods.router import router as payment_methods_router

router = APIRouter()

# Include sub-module routers
router.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
router.include_router(categories_router, prefix="/categories", tags=["categories"])
router.include_router(payment_methods_router, prefix="/payment-methods", tags=["payment-methods"])
