from fastapi import Depends

from src.auth.dependencies import require_permissions, get_api_key, require_user_permissions
from src.auth.enums.actions import Actions
from src.auth.enums.features import Features
from src.core.database import get_db
from src.auth.jwt_dependencies import get_current_active_user


def get_feature_permissions(feature: Features, action: Actions):
    """
    Returns a dependency that checks permissions for the specified feature and action.

    Usage:
        @router.get("/", dependencies=[Depends(get_feature_permissions(Features.CATEGORIES, Actions.READ))])
    """
    return lambda api_key=Depends(get_api_key), db=Depends(get_db): require_permissions(
        feature, action, api_key, db
    )


def get_expenses_permissions(action: Actions):
    """Returns a dependency that checks permissions for the expenses feature."""
    return get_feature_permissions(Features.EXPENSES, action)


# Add more feature-specific permissions helpers as needed
def get_categories_permissions(action: Actions):
    """Returns a dependency that checks permissions for the categories feature."""
    return get_feature_permissions(Features.CATEGORIES, action)


def get_payment_methods_permissions(action: Actions):
    """Returns a dependency that checks permissions for the payment methods feature."""
    return get_feature_permissions(Features.PAYMENT_METHODS, action)


def get_todo_items_permissions(action: Actions):
    """Returns a dependency that checks permissions for the todo items feature."""
    return get_feature_permissions(Features.TODO_ITEMS, action)


def get_api_keys_permissions(action: Actions):
    """Returns a dependency that checks permissions for the API keys feature."""
    return get_feature_permissions(Features.API_KEYS, action)


def get_shared_permissions(action: Actions):
    """Returns a dependency that checks permissions for the shared feature."""
    return get_feature_permissions(Features.SHARED, action)


def get_user_feature_permissions(feature: Features, action: Actions):
    """
    Returns a dependency that checks user permissions for the specified feature and action.

    Usage:
        @router.get("/", dependencies=[Depends(get_user_feature_permissions(Features.CATEGORIES, Actions.READ))])
    """
    return lambda current_user=Depends(get_current_active_user), db=Depends(get_db): require_user_permissions(
        feature, action, current_user, db
    )


def get_user_expenses_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the expenses feature."""
    return get_user_feature_permissions(Features.EXPENSES, action)


def get_user_categories_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the categories feature."""
    return get_user_feature_permissions(Features.CATEGORIES, action)


def get_user_payment_methods_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the payment methods feature."""
    return get_user_feature_permissions(Features.PAYMENT_METHODS, action)


def get_user_todo_items_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the todo items feature."""
    return get_user_feature_permissions(Features.TODO_ITEMS, action)


def get_user_api_keys_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the API keys feature."""
    return get_user_feature_permissions(Features.API_KEYS, action)


def get_user_shared_permissions(action: Actions):
    """Returns a dependency that checks user permissions for the shared feature."""
    return get_user_feature_permissions(Features.SHARED, action)
