"""Categories domain permission dependencies."""

from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features


def get_categories_permissions(action: Actions):
    """User-based categories permissions dependency."""
    return require_permission(Features.CATEGORIES, action)