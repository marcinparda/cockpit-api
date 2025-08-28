"""Domain service for feature-specific permission helpers."""

from src.services.authorization.shared.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features


def get_expenses_permissions(action: Actions):
    """User-based expenses permissions dependency."""
    return require_permission(Features.EXPENSES, action)


def get_categories_permissions(action: Actions):
    """User-based categories permissions dependency."""
    return require_permission(Features.CATEGORIES, action)


def get_payment_methods_permissions(action: Actions):
    """User-based payment methods permissions dependency."""
    return require_permission(Features.PAYMENT_METHODS, action)


def get_todo_items_permissions(action: Actions):
    """User-based todo items permissions dependency."""
    return require_permission(Features.TODO_ITEMS, action)
