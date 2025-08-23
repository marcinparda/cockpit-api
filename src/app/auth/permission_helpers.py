
from fastapi import Depends

from src.app.auth.dependencies import require_user_permissions
from src.app.auth.jwt_dependencies import get_current_active_user
from src.core.database import get_db
from src.app.auth.enums.actions import Actions
from src.app.auth.enums.features import Features


def get_feature_permissions(feature: Features, action: Actions):
    """
    Generic user permission dependency for any feature/action combination.

    Args:
        feature: Feature to check permission for
        action: Action to check permission for

    Returns:
        FastAPI dependency that requires user permission
    """
    async def dependency(
        current_user=Depends(get_current_active_user),
        db=Depends(get_db)
    ):
        return await require_user_permissions(feature, action, current_user, db)
    return dependency


def get_expenses_permissions(action: Actions):
    """User-based expenses permissions dependency."""
    return get_feature_permissions(Features.EXPENSES, action)


def get_categories_permissions(action: Actions):
    """User-based categories permissions dependency."""
    return get_feature_permissions(Features.CATEGORIES, action)


def get_payment_methods_permissions(action: Actions):
    """User-based payment methods permissions dependency."""
    return get_feature_permissions(Features.PAYMENT_METHODS, action)


def get_todo_items_permissions(action: Actions):
    """User-based todo items permissions dependency."""
    return get_feature_permissions(Features.TODO_ITEMS, action)


