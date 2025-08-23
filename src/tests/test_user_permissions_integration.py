"""Simple integration test for user permission system."""

import pytest
from src.app.auth.permissions import check_user_permissions, get_user_permissions
from src.app.auth.permission_helpers import (
    get_feature_permissions,
    get_expenses_permissions,
    get_categories_permissions,
    get_payment_methods_permissions,
    get_todo_items_permissions
)
from src.app.auth.dependencies import require_user_permissions, require_admin_role
from src.app.auth.enums.features import Features
from src.app.auth.enums.actions import Actions


class TestUserPermissionSystemIntegration:
    """Test user permission system integration."""

    def test_user_permission_functions_exist(self):
        """Test that all user permission functions exist and are callable."""
        # Test permission checking functions
        assert callable(check_user_permissions)
        assert callable(get_user_permissions)

        # Test permission helpers
        assert callable(get_feature_permissions)
        assert callable(get_expenses_permissions)
        assert callable(get_categories_permissions)
        assert callable(get_payment_methods_permissions)
        assert callable(get_todo_items_permissions)

        # Test dependencies
        assert callable(require_user_permissions)
        assert callable(require_admin_role)

    def test_user_permission_helpers_create_dependencies(self):
        """Test that user permission helpers create proper dependencies."""
        # Test creating permission dependencies
        expenses_create_dep = get_expenses_permissions(Actions.CREATE)
        expenses_read_dep = get_expenses_permissions(Actions.READ)
        categories_update_dep = get_categories_permissions(Actions.UPDATE)

        # All should be callable
        assert callable(expenses_create_dep)
        assert callable(expenses_read_dep)
        assert callable(categories_update_dep)

    def test_user_permission_helpers_use_correct_features(self):
        """Test that permission helpers use the correct feature enums."""
        # Test that helpers are created with correct feature types
        feature_dep = get_feature_permissions(
            Features.EXPENSES, Actions.READ)
        assert callable(feature_dep)

        # Test specific feature helpers exist
        assert callable(get_expenses_permissions(Actions.READ))
        assert callable(get_categories_permissions(Actions.CREATE))
        assert callable(get_payment_methods_permissions(Actions.UPDATE))
        assert callable(get_todo_items_permissions(Actions.DELETE))

    def test_permission_system_architecture(self):
        """Test that the permission system has proper architecture."""
        # Import all necessary components
        from src.app.auth.permissions import (
            check_user_permissions,
            get_user_permissions,
            user_has_admin_role,
            get_admin_permissions
        )
        from src.app.auth.permission_helpers import get_feature_permissions
        from src.app.auth.dependencies import require_user_permissions, require_admin_role

        # Test that all components exist
        assert check_user_permissions is not None
        assert get_user_permissions is not None
        assert user_has_admin_role is not None
        assert get_admin_permissions is not None
        assert get_feature_permissions is not None
        assert require_user_permissions is not None
        assert require_admin_role is not None

    def test_user_service_functions_exist(self):
        """Test that user service functions exist."""
        assert callable(get_user_permissions)

    def test_enums_work_with_permission_system(self):
        """Test that feature and action enums work with permission system."""
        # Test that all feature enums can be used
        features = [
            Features.EXPENSES,
            Features.CATEGORIES,
            Features.PAYMENT_METHODS,
            Features.TODO_ITEMS,
        ]

        actions = [
            Actions.CREATE,
            Actions.READ,
            Actions.UPDATE,
            Actions.DELETE
        ]

        # Test that permission helpers can be created for all combinations
        for feature in features:
            for action in actions:
                dep = get_feature_permissions(feature, action)
                assert callable(dep)

    def test_permission_system_imports_work(self):
        """Test that all permission system imports work correctly."""
        # Test imports from different modules
        from src.app.auth.permissions import check_user_permissions
        from src.app.auth.dependencies import require_user_permissions

        # All should be imported successfully
        assert check_user_permissions is not None
        assert require_user_permissions is not None
