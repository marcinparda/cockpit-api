"""Payment methods domain permission dependencies."""

from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features


def get_payment_methods_permissions(action: Actions):
    """User-based payment methods permissions dependency."""
    return require_permission(Features.PAYMENT_METHODS, action)