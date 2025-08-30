"""Expenses domain permission dependencies."""

from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features


def get_expenses_permissions(action: Actions):
    """User-based expenses permissions dependency."""
    return require_permission(Features.EXPENSES, action)