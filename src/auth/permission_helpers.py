from fastapi import Depends
from functools import partial

from src.auth.dependencies import require_user_permissions
from src.auth.enums.actions import Actions
from src.auth.enums.features import Features


def get_feature_permissions(feature: Features, action: Actions):
    """
    Generic user permission dependency for any feature/action combination.

    Args:
        feature: Feature to check permission for
        action: Action to check permission for

    Returns:
        FastAPI dependency that requires user permission
    """
    return partial(require_user_permissions, feature, action)


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


def get_api_keys_permissions(action: Actions):
    """User-based API keys permissions dependency."""
    return get_feature_permissions(Features.API_KEYS, action)


def get_shared_permissions(action: Actions):
    """User-based shared permissions dependency."""
    return get_feature_permissions(Features.SHARED, action)
