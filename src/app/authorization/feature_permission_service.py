
from src.app.authorization.dependencies import require_permission
from src.app.authorization.enums.actions import Actions
from src.app.authorization.enums.features import Features


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
